from __future__ import annotations

import threading
import time
from datetime import datetime

from .model_index import ModelIndex
from .models import AppConfig, ScheduleRule
from .runtime import RuntimeManager


def _minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def _matches(rule: ScheduleRule, now_minutes: int) -> bool:
    start = _minutes(rule.start)
    end = _minutes(rule.end)
    if start == end:
        return True
    if start < end:
        return start <= now_minutes < end
    return now_minutes >= start or now_minutes < end


class ScheduleController:
    def __init__(self, config: AppConfig, index: ModelIndex, runtime: RuntimeManager) -> None:
        self.config = config
        self.index = index
        self.runtime = runtime
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="vmlx-station-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def active_rule(self) -> ScheduleRule | None:
        if not self.config.schedule.enabled:
            return None
        now = datetime.now()
        now_minutes = now.hour * 60 + now.minute
        for rule in self.config.schedule.rules:
            if _matches(rule, now_minutes):
                return rule
        return None

    def apply_if_needed(self) -> None:
        rule = self.active_rule()
        if not rule:
            return
        model = self.index.get(rule.model_id)
        if not model:
            return
        current = self.runtime.status(schedule_rule=rule)
        if current.loaded_model_id != model.id:
            self.runtime.load(model, reason=f"schedule:{rule.name}")

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.apply_if_needed()
            except Exception:
                pass
            self._stop.wait(60)

