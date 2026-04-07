from __future__ import annotations

import json
from pathlib import Path

from .models import InstalledModel


class ModelIndex:
    def __init__(self, model_roots: list[str]) -> None:
        self.model_roots = [Path(root).expanduser() for root in model_roots]
        self._cache: list[InstalledModel] = []

    def scan(self) -> list[InstalledModel]:
        items: list[InstalledModel] = []
        for root in self.model_roots:
            if not root.exists():
                continue
            for child in sorted(root.rglob("*")):
                if not child.is_dir():
                    continue
                config_path = child / "config.json"
                jang_path = child / "jang_config.json"
                if not config_path.exists() and not jang_path.exists():
                    continue
                items.append(self._build_model(child, config_path, jang_path))
        unique: dict[str, InstalledModel] = {}
        for item in items:
            unique[item.id] = item
        self._cache = sorted(unique.values(), key=lambda item: item.name.lower())
        return list(self._cache)

    def list(self) -> list[InstalledModel]:
        if not self._cache:
            return self.scan()
        return list(self._cache)

    def get(self, model_id: str) -> InstalledModel | None:
        for model in self.list():
            if model.id == model_id:
                return model
        return None

    def _build_model(self, path: Path, config_path: Path, jang_path: Path) -> InstalledModel:
        config = {}
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                config = {}

        text_config = config.get("text_config") if isinstance(config.get("text_config"), dict) else {}
        vision_config = config.get("vision_config") if isinstance(config.get("vision_config"), dict) else {}

        name = config.get("_name_or_path") or path.name
        source = path.parent.name
        has_vision = bool(vision_config)
        has_jang = jang_path.exists()
        engine = "jang-vmlx" if has_jang else "mlx-vmlx"
        model_id = path.name
        architecture = None
        architectures = config.get("architectures")
        if isinstance(architectures, list) and architectures:
            first = architectures[0]
            if isinstance(first, str):
                architecture = first

        text_context_tokens = text_config.get("max_position_embeddings")
        if not isinstance(text_context_tokens, int):
            text_context_tokens = config.get("max_position_embeddings")
        if not isinstance(text_context_tokens, int):
            text_context_tokens = None

        vision_context_tokens = vision_config.get("max_position_embeddings")
        if not isinstance(vision_context_tokens, int):
            vision_context_tokens = None

        return InstalledModel(
            id=model_id,
            name=str(name),
            path=str(path),
            engine=engine,
            source=source,
            model_type=str(config.get("model_type")) if config.get("model_type") else None,
            architecture=architecture,
            text_context_tokens=text_context_tokens,
            vision_context_tokens=vision_context_tokens,
            has_jang=has_jang,
            has_vision=has_vision,
        )
