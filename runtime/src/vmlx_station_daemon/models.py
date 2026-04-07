from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class InstalledModel(BaseModel):
    id: str
    name: str
    path: str
    engine: str
    source: str
    has_jang: bool = False
    has_vision: bool = False


class ScheduleRule(BaseModel):
    name: str
    start: str
    end: str
    model_id: str


class ScheduleConfig(BaseModel):
    enabled: bool = False
    rules: list[ScheduleRule] = Field(default_factory=list)


class ControlAPIConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 18100


class RuntimeConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 18083
    vmlx_bin: str = "/Users/jaesik/.venvs/vmlx/bin/vmlx"
    api_key: Optional[str] = None
    default_enable_thinking: bool = False
    max_tokens: int = 32768
    max_num_seqs: int = 256
    continuous_batching: bool = False
    enable_prefix_cache: bool = True
    cache_memory_percent: float = 0.30
    use_paged_cache: bool = False
    paged_cache_block_size: int = 64
    max_cache_blocks: int = 1000
    kv_cache_quantization: str = "none"
    kv_cache_group_size: int = 64
    stream_from_disk: bool = False
    stream_memory_percent: int = 90
    extra_args: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    model_roots: list[str] = Field(default_factory=list)
    control_api: ControlAPIConfig = Field(default_factory=ControlAPIConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)


class LoadRequest(BaseModel):
    model_id: str


class ChatTestRequest(BaseModel):
    prompt: str
    system_prompt: str = ""
    max_tokens: int = 256
    temperature: Optional[float] = None


class RuntimeStatus(BaseModel):
    running: bool
    loaded_model_id: Optional[str] = None
    loaded_model_name: Optional[str] = None
    served_model_name: Optional[str] = None
    runtime_pid: Optional[int] = None
    runtime_port: int
    openai_base_url: str
    control_base_url: str
    schedule_enabled: bool
    active_schedule_rule: Optional[ScheduleRule] = None
    message: str
