from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

from .config import AppPaths
from .models import AppConfig, InstalledModel, RuntimeStatus, ScheduleRule


def _slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part)


class RuntimeManager:
    def __init__(self, config: AppConfig, paths: AppPaths) -> None:
        self.config = config
        self.paths = paths
        self.paths.ensure()
        self._process: subprocess.Popen[str] | None = None
        self._managed_pid: int | None = None
        self._loaded_model: InstalledModel | None = None
        self._served_model_name: str | None = None
        self._recover_state()

    def load(self, model: InstalledModel, *, reason: str = "manual") -> RuntimeStatus:
        if self.is_running() and self._loaded_model and self._loaded_model.id == model.id:
            self._loaded_model = model
            self._served_model_name = self._served_model_name or _slugify(model.id)
            self._write_state(reason=f"refresh-{reason}")
            return self.status(message=f"{model.name} already running ({reason})")

        self._validate_model_runtime_compatibility(model)
        self.unload()
        log_path = self.paths.log_dir / "runtime.log"
        log_handle = log_path.open("a", encoding="utf-8")

        served_model_name = _slugify(model.id)
        cmd = [
            self.config.runtime.vmlx_bin,
            "serve",
            model.path,
            "--host",
            self.config.runtime.host,
            "--port",
            str(self.config.runtime.port),
            "--served-model-name",
            served_model_name,
            "--default-enable-thinking",
            str(self.config.runtime.default_enable_thinking).lower(),
            "--max-tokens",
            str(self.config.runtime.max_tokens),
            "--max-num-seqs",
            str(self.config.runtime.max_num_seqs),
            "--cache-memory-percent",
            str(self.config.runtime.cache_memory_percent),
            "--paged-cache-block-size",
            str(self.config.runtime.paged_cache_block_size),
            "--max-cache-blocks",
            str(self.config.runtime.max_cache_blocks),
            "--kv-cache-quantization",
            self.config.runtime.kv_cache_quantization,
            "--kv-cache-group-size",
            str(self.config.runtime.kv_cache_group_size),
            "--stream-memory-percent",
            str(self.config.runtime.stream_memory_percent),
        ]
        if self.config.runtime.continuous_batching:
            cmd.append("--continuous-batching")
        if self.config.runtime.enable_prefix_cache:
            cmd.append("--enable-prefix-cache")
        else:
            cmd.append("--disable-prefix-cache")
        if self.config.runtime.use_paged_cache:
            cmd.append("--use-paged-cache")
        if self.config.runtime.stream_from_disk:
            cmd.append("--stream-from-disk")
        if self.config.runtime.api_key:
            cmd.extend(["--api-key", self.config.runtime.api_key])
        cmd.extend(self.config.runtime.extra_args)

        self._process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        self._managed_pid = self._process.pid
        self._loaded_model = model
        self._served_model_name = served_model_name
        self._wait_for_port(self.config.runtime.host, self.config.runtime.port, timeout=180)
        self._write_state(reason=reason)
        return self.status(message=f"Loaded {model.name} ({reason})")

    def unload(self) -> None:
        pid = self._runtime_pid()
        if pid:
            self._terminate_pid(pid)
        self._process = None
        self._managed_pid = None
        self._loaded_model = None
        self._served_model_name = None
        self._write_state(reason="unload")

    def is_running(self) -> bool:
        return self._runtime_pid() is not None

    def status(self, *, schedule_rule: ScheduleRule | None = None, message: str = "Idle") -> RuntimeStatus:
        runtime_pid = self._runtime_pid()
        loaded_model_id = self._loaded_model.id if self._loaded_model else None
        loaded_model_name = self._loaded_model.name if self._loaded_model else None
        warnings: list[str] = []
        if self._loaded_model and self._loaded_model.text_context_tokens:
            if self.config.runtime.max_tokens > self._loaded_model.text_context_tokens:
                warnings.append(
                    "Configured max_tokens is higher than the loaded model's text context window."
                )
        return RuntimeStatus(
            running=runtime_pid is not None,
            loaded_model_id=loaded_model_id,
            loaded_model_name=loaded_model_name,
            served_model_name=self._served_model_name,
            loaded_model_text_context_tokens=(
                self._loaded_model.text_context_tokens if self._loaded_model else None
            ),
            loaded_model_vision_context_tokens=(
                self._loaded_model.vision_context_tokens if self._loaded_model else None
            ),
            runtime_pid=runtime_pid,
            runtime_port=self.config.runtime.port,
            openai_base_url=f"http://{self.config.runtime.host}:{self.config.runtime.port}/v1",
            control_base_url=f"http://{self.config.control_api.host}:{self.config.control_api.port}",
            schedule_enabled=self.config.schedule.enabled,
            active_schedule_rule=schedule_rule,
            warnings=warnings,
            message=message,
        )

    def _write_state(self, *, reason: str) -> None:
        runtime_pid = self._runtime_pid()
        payload = {
            "running": runtime_pid is not None,
            "pid": runtime_pid,
            "loaded_model": self._loaded_model.model_dump() if self._loaded_model else None,
            "served_model_name": self._served_model_name,
            "reason": reason,
            "openai_base_url": f"http://{self.config.runtime.host}:{self.config.runtime.port}/v1",
        }
        self.paths.runtime_state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _wait_for_port(host: str, port: int, *, timeout: int) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                if sock.connect_ex((host, port)) == 0:
                    return
            time.sleep(1)
        raise TimeoutError(f"Timed out waiting for {host}:{port}")

    def _recover_state(self) -> None:
        path = self.paths.runtime_state_path
        payload: dict[str, object] = {}
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}

        pid = payload.get("pid")
        if (
            isinstance(pid, int)
            and self._pid_alive(pid)
            and self._port_open(self.config.runtime.host, self.config.runtime.port)
        ):
            self._managed_pid = pid
            loaded_model = payload.get("loaded_model")
            if isinstance(loaded_model, dict):
                try:
                    self._loaded_model = InstalledModel.model_validate(loaded_model)
                except Exception:
                    self._loaded_model = None
            else:
                loaded_model_id = payload.get("loaded_model_id")
                loaded_model_name = payload.get("loaded_model_name")
                if isinstance(loaded_model_id, str) and isinstance(loaded_model_name, str):
                    self._loaded_model = InstalledModel(
                        id=loaded_model_id,
                        name=loaded_model_name,
                        path="unknown",
                        engine="unknown",
                        source="recovered-state",
                    )
            served_model_name = payload.get("served_model_name")
            if isinstance(served_model_name, str):
                self._served_model_name = served_model_name
            return

        self._recover_from_live_runtime()

    def _runtime_pid(self) -> int | None:
        if self._process is not None:
            if self._process.poll() is None:
                self._managed_pid = self._process.pid
                return self._process.pid
            self._process = None

        if self._managed_pid and self._pid_alive(self._managed_pid) and self._port_open(
            self.config.runtime.host, self.config.runtime.port
        ):
            return self._managed_pid
        return None

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    @staticmethod
    def _port_open(host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            return sock.connect_ex((host, port)) == 0

    @staticmethod
    def _terminate_pid(pid: int) -> None:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except ProcessLookupError:
            return
        deadline = time.time() + 10
        while time.time() < deadline:
            if not RuntimeManager._pid_alive(pid):
                return
            time.sleep(0.25)
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except ProcessLookupError:
            return

    def _recover_from_live_runtime(self) -> None:
        if not self._port_open(self.config.runtime.host, self.config.runtime.port):
            return

        pid = self._listener_pid(self.config.runtime.port)
        if pid:
            self._managed_pid = pid

        live_model_id = self._live_model_id()
        if live_model_id:
            self._loaded_model = InstalledModel(
                id=live_model_id,
                name=live_model_id,
                path="unknown",
                engine="unknown",
                source="recovered-live",
            )
            self._served_model_name = _slugify(live_model_id)

    def _validate_model_runtime_compatibility(self, model: InstalledModel) -> None:
        text_context = model.text_context_tokens
        if text_context and self.config.runtime.max_tokens > text_context:
            raise ValueError(
                f"Configured max_tokens ({self.config.runtime.max_tokens}) exceeds "
                f"{model.id}'s text context window ({text_context}). "
                "Lower max_tokens before loading this model."
            )

    @staticmethod
    def _listener_pid(port: int) -> int | None:
        try:
            output = subprocess.check_output(
                ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except subprocess.CalledProcessError:
            return None
        if not output:
            return None
        first = output.splitlines()[0].strip()
        return int(first) if first.isdigit() else None

    def _live_model_id(self) -> str | None:
        url = f"http://{self.config.runtime.host}:{self.config.runtime.port}/v1/models"
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                payload = json.load(response)
        except Exception:
            return None
        data = payload.get("data")
        if not isinstance(data, list) or not data:
            return None
        first = data[0]
        if not isinstance(first, dict):
            return None
        model_id = first.get("id")
        if isinstance(model_id, str):
            return model_id
        return None
