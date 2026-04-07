from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class InstalledModel(BaseModel):
    id: str
    name: str
    path: str
    engine: str
    source: str
    model_type: Optional[str] = None
    architecture: Optional[str] = None
    text_context_tokens: Optional[int] = None
    vision_context_tokens: Optional[int] = None
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


class OpenWebUIConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 3000


class RuntimeConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 18083
    vmlx_bin: str = "/Users/jaesik/.venvs/vmlx/bin/vmlx"
    api_key: Optional[str] = None
    default_enable_thinking: bool = False
    max_tokens: int = Field(default=262144, ge=1, le=262144)
    max_num_seqs: int = Field(default=256, ge=1, le=4096)
    continuous_batching: bool = True
    enable_prefix_cache: bool = True
    cache_memory_percent: float = Field(default=0.30, gt=0.0, le=0.95)
    use_paged_cache: bool = False
    paged_cache_block_size: int = Field(default=64, ge=1, le=4096)
    max_cache_blocks: int = Field(default=1000, ge=1, le=1_000_000)
    kv_cache_quantization: Literal["none", "q4", "q8"] = "q4"
    kv_cache_group_size: int = Field(default=64, ge=1, le=4096)
    stream_from_disk: bool = False
    stream_memory_percent: int = Field(default=90, ge=1, le=99)
    extra_args: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_runtime_constraints(self) -> "RuntimeConfig":
        if self.kv_cache_quantization != "none" and not self.continuous_batching:
            raise ValueError("KV cache quantization requires continuous batching.")
        if self.use_paged_cache and not self.continuous_batching:
            raise ValueError("Paged cache requires continuous batching.")
        if self.stream_from_disk:
            if self.max_num_seqs != 1:
                raise ValueError("Stream-from-disk mode requires max_num_seqs=1.")
            if self.continuous_batching:
                raise ValueError("Stream-from-disk mode cannot be combined with continuous batching.")
            if self.enable_prefix_cache:
                raise ValueError("Stream-from-disk mode cannot be combined with prefix cache.")
            if self.use_paged_cache:
                raise ValueError("Stream-from-disk mode cannot be combined with paged cache.")
            if self.kv_cache_quantization != "none":
                raise ValueError("Stream-from-disk mode cannot be combined with KV cache quantization.")
        return self


class AppConfig(BaseModel):
    model_roots: list[str] = Field(default_factory=list)
    control_api: ControlAPIConfig = Field(default_factory=ControlAPIConfig)
    open_webui: OpenWebUIConfig = Field(default_factory=OpenWebUIConfig)
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
    loaded_model_text_context_tokens: Optional[int] = None
    loaded_model_vision_context_tokens: Optional[int] = None
    runtime_pid: Optional[int] = None
    runtime_port: int
    openai_base_url: str
    control_base_url: str
    open_webui_url: Optional[str] = None
    open_webui_running: bool = False
    schedule_enabled: bool
    active_schedule_rule: Optional[ScheduleRule] = None
    warnings: list[str] = Field(default_factory=list)
    message: str
