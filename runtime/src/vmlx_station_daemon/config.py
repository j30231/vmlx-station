from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import AppConfig


@dataclass(slots=True)
class AppPaths:
    support_dir: Path
    config_path: Path
    state_dir: Path
    runtime_state_path: Path
    log_dir: Path

    @classmethod
    def default(cls) -> "AppPaths":
        support_dir = Path.home() / "Library" / "Application Support" / "vmlx-station"
        state_dir = support_dir / "state"
        log_dir = support_dir / "logs"
        return cls(
            support_dir=support_dir,
            config_path=support_dir / "config.yaml",
            state_dir=state_dir,
            runtime_state_path=state_dir / "runtime.json",
            log_dir=log_dir,
        )

    def ensure(self) -> None:
        self.support_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


def load_config(paths: AppPaths) -> AppConfig:
    paths.ensure()
    if not paths.config_path.exists():
        return AppConfig(
            model_roots=[
                "/Users/jaesik/llm/gguf",
                "/Users/jaesik/llm/llm-models",
            ]
        )

    payload = yaml.safe_load(paths.config_path.read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(payload)


def save_config(paths: AppPaths, config: AppConfig) -> None:
    paths.ensure()
    paths.config_path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )

