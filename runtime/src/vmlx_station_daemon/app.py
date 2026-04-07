from __future__ import annotations

import json
import urllib.request

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .admin_ui import render_admin_ui
from .config import AppPaths, load_config, save_config
from .model_index import ModelIndex
from .models import AppConfig, ChatTestRequest, LoadRequest, RuntimeStatus, ScheduleConfig
from .runtime import RuntimeManager
from .scheduler import ScheduleController


def create_app() -> FastAPI:
    paths = AppPaths.default()
    config = load_config(paths)
    model_index = ModelIndex(config.model_roots)
    runtime = RuntimeManager(config, paths)
    scheduler = ScheduleController(config, model_index, runtime)

    app = FastAPI(title="vMLX Station Daemon", version="0.1.0")
    app.state.paths = paths
    app.state.config = config
    app.state.model_index = model_index
    app.state.runtime = runtime
    app.state.scheduler = scheduler

    @app.on_event("startup")
    async def startup() -> None:
        model_index.scan()
        scheduler.start()
        scheduler.apply_if_needed()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        scheduler.stop()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def root() -> HTMLResponse:
        return HTMLResponse(render_admin_ui())

    @app.get("/admin", response_class=HTMLResponse)
    async def admin() -> HTMLResponse:
        return HTMLResponse(render_admin_ui())

    @app.get("/api/status", response_model=RuntimeStatus)
    async def status() -> RuntimeStatus:
        runtime: RuntimeManager = app.state.runtime
        scheduler: ScheduleController = app.state.scheduler
        rule = scheduler.active_rule()
        return runtime.status(schedule_rule=rule, message=_status_message(runtime, rule))

    @app.get("/api/models")
    async def models() -> dict[str, object]:
        model_index: ModelIndex = app.state.model_index
        items = model_index.scan()
        return {"items": [item.model_dump() for item in items], "count": len(items)}

    @app.post("/api/load", response_model=RuntimeStatus)
    async def load_model(request: LoadRequest) -> RuntimeStatus:
        model_index: ModelIndex = app.state.model_index
        runtime: RuntimeManager = app.state.runtime
        model = model_index.get(request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
        return runtime.load(model)

    @app.post("/api/unload")
    async def unload_model() -> dict[str, str]:
        runtime: RuntimeManager = app.state.runtime
        runtime.unload()
        return {"status": "ok"}

    @app.post("/api/reload", response_model=RuntimeStatus)
    async def reload_model() -> RuntimeStatus:
        runtime: RuntimeManager = app.state.runtime
        model_index: ModelIndex = app.state.model_index
        current = runtime.status()
        model_id = current.loaded_model_id
        if not model_id:
            raise HTTPException(status_code=409, detail="No loaded model to reload")
        model = model_index.get(model_id)
        if not model:
            raise HTTPException(status_code=409, detail=f"Loaded model not found in index: {model_id}")
        return runtime.load(model, reason="reload")

    @app.post("/api/rescan")
    async def rescan() -> dict[str, object]:
        model_index: ModelIndex = app.state.model_index
        items = model_index.scan()
        return {"status": "ok", "count": len(items)}

    @app.get("/api/config", response_model=AppConfig)
    async def get_config() -> AppConfig:
        return app.state.config

    @app.put("/api/config", response_model=AppConfig)
    async def put_config(config: AppConfig) -> AppConfig:
        _apply_config(app, config)
        return app.state.config

    @app.get("/api/schedule", response_model=ScheduleConfig)
    async def get_schedule() -> ScheduleConfig:
        return app.state.config.schedule

    @app.put("/api/schedule", response_model=ScheduleConfig)
    async def put_schedule(schedule: ScheduleConfig) -> ScheduleConfig:
        current_config: AppConfig = app.state.config
        new_config = AppConfig.model_validate(
            {**current_config.model_dump(), "schedule": schedule.model_dump()}
        )
        _apply_config(app, new_config)
        app.state.scheduler.apply_if_needed()
        return app.state.config.schedule

    @app.post("/api/chat-test")
    async def chat_test(request: ChatTestRequest) -> dict[str, object]:
        runtime: RuntimeManager = app.state.runtime
        if not runtime.is_running():
            raise HTTPException(status_code=409, detail="No model is currently loaded")

        status = runtime.status()
        model_name = status.served_model_name or status.loaded_model_id
        if not model_name:
            raise HTTPException(status_code=409, detail="Loaded model is unknown")

        messages = []
        if request.system_prompt.strip():
            messages.append({"role": "system", "content": request.system_prompt.strip()})
        messages.append({"role": "user", "content": request.prompt})
        payload: dict[str, object] = {
            "model": model_name,
            "messages": messages,
            "max_tokens": request.max_tokens,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature

        api_url = f"{status.openai_base_url}/chat/completions"
        body = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            api_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=300) as response:
                chat_payload = json.load(response)
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"Chat test failed: {error}") from error

        content = ""
        try:
            content = chat_payload["choices"][0]["message"]["content"]
        except Exception:
            content = ""
        return {"model": model_name, "content": content, "raw": chat_payload}

    return app


def _apply_config(app: FastAPI, config: AppConfig) -> None:
    paths: AppPaths = app.state.paths
    runtime: RuntimeManager = app.state.runtime
    scheduler: ScheduleController = app.state.scheduler

    new_model_index = ModelIndex(config.model_roots)
    new_model_index.scan()

    app.state.config = config
    app.state.model_index = new_model_index
    runtime.config = config
    scheduler.config = config
    scheduler.index = new_model_index
    save_config(paths, config)


def _status_message(runtime: RuntimeManager, rule) -> str:
    status = runtime.status(schedule_rule=rule)
    if status.running and status.loaded_model_name:
        return f"Loaded {status.loaded_model_name}"
    if rule:
        return f"Idle; next scheduled model {rule.model_id}"
    return "Idle"
