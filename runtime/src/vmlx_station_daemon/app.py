from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .config import AppPaths, load_config, save_config
from .model_index import ModelIndex
from .models import AppConfig, LoadRequest, RuntimeStatus, ScheduleConfig
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

    @app.get("/api/status", response_model=RuntimeStatus)
    async def status() -> RuntimeStatus:
        rule = scheduler.active_rule()
        return runtime.status(schedule_rule=rule, message=_status_message(runtime, rule))

    @app.get("/api/models")
    async def models() -> dict[str, object]:
        items = model_index.scan()
        return {"items": [item.model_dump() for item in items], "count": len(items)}

    @app.post("/api/load", response_model=RuntimeStatus)
    async def load_model(request: LoadRequest) -> RuntimeStatus:
        model = model_index.get(request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
        return runtime.load(model)

    @app.post("/api/unload")
    async def unload_model() -> dict[str, str]:
        runtime.unload()
        return {"status": "ok"}

    @app.post("/api/rescan")
    async def rescan() -> dict[str, object]:
        items = model_index.scan()
        return {"status": "ok", "count": len(items)}

    @app.get("/api/schedule", response_model=ScheduleConfig)
    async def get_schedule() -> ScheduleConfig:
        return app.state.config.schedule

    @app.put("/api/schedule", response_model=ScheduleConfig)
    async def put_schedule(schedule: ScheduleConfig) -> ScheduleConfig:
        current_config: AppConfig = app.state.config
        new_config = AppConfig.model_validate(
            {**current_config.model_dump(), "schedule": schedule.model_dump()}
        )
        app.state.config = new_config
        runtime.config = new_config
        scheduler.config = new_config
        save_config(paths, new_config)
        scheduler.apply_if_needed()
        return new_config.schedule

    return app


def _status_message(runtime: RuntimeManager, rule) -> str:
    status = runtime.status(schedule_rule=rule)
    if status.running and status.loaded_model_name:
        return f"Loaded {status.loaded_model_name}"
    if rule:
        return f"Idle; next scheduled model {rule.model_id}"
    return "Idle"
