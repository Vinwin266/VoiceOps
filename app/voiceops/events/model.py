from pydantic import BaseModel


class VoiceOpsEvent(BaseModel):
    event_id: str
    run_id: int | None = None
    timestamp: str | None = None
    level: str | None = None
    module: str | None = None
    phase: str | None = None
    pipeline_node: str | None = None
    call_sid: str | None = None
    room_id: str | None = None
    agent_id: str | None = None
    turn_id: str | None = None
    provider: str | None = None
    latency_ms: int | None = None
    error_type: str | None = None
    message_redacted: str
    raw_message: str
    fingerprint: str | None = None
