from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
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
        self._loaded_model: InstalledModel | None = None
        self._served_model_name: str | None = None

    def load(self, model: InstalledModel, *, reason: str = "manual") -> RuntimeStatus:
        if self.is_running() and self._loaded_model and self._loaded_model.id == model.id:
            return self.status(message=f"{model.name} already running ({reason})")

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
        ]
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
        self._loaded_model = model
        self._served_model_name = served_model_name
        self._wait_for_port(self.config.runtime.host, self.config.runtime.port, timeout=180)
        self._write_state(reason=reason)
        return self.status(message=f"Loaded {model.name} ({reason})")

    def unload(self) -> None:
        if self._process and self._process.poll() is None:
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                self._process.wait(timeout=5)
        self._process = None
        self._loaded_model = None
        self._served_model_name = None
        self._write_state(reason="unload")

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def status(self, *, schedule_rule: ScheduleRule | None = None, message: str = "Idle") -> RuntimeStatus:
        runtime_pid = self._process.pid if self.is_running() else None
        loaded_model_id = self._loaded_model.id if self._loaded_model else None
        loaded_model_name = self._loaded_model.name if self._loaded_model else None
        return RuntimeStatus(
            running=self.is_running(),
            loaded_model_id=loaded_model_id,
            loaded_model_name=loaded_model_name,
            served_model_name=self._served_model_name,
            runtime_pid=runtime_pid,
            runtime_port=self.config.runtime.port,
            openai_base_url=f"http://{self.config.runtime.host}:{self.config.runtime.port}/v1",
            control_base_url=f"http://{self.config.control_api.host}:{self.config.control_api.port}",
            schedule_enabled=self.config.schedule.enabled,
            active_schedule_rule=schedule_rule,
            message=message,
        )

    def _write_state(self, *, reason: str) -> None:
        payload = {
            "running": self.is_running(),
            "pid": self._process.pid if self.is_running() else None,
            "loaded_model_id": self._loaded_model.id if self._loaded_model else None,
            "loaded_model_name": self._loaded_model.name if self._loaded_model else None,
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

