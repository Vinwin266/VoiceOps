from pydantic import BaseModel


class VoiceOpsEvent(BaseModel):
    event_id: str
    run_id: int | None = None
    timestamp: str | None = None
    source_system: str | None = None
    source_module: str | None = None
    canonical_module: str | None = None
    level: str | None = None
    module: str | None = None
    phase: str | None = None
    pipeline_node: str | None = None
    call_sid: str | None = None
    provider_call_id: str | None = None
    sip_call_id: str | None = None
    room_id: str | None = None
    agent_id: str | None = None
    participant_id: str | None = None
    turn_id: str | None = None
    provider: str | None = None
    protocol: str | None = None
    direction: str | None = None
    from_number: str | None = None
    to_number: str | None = None
    status_code: str | None = None
    hangup_cause: str | None = None
    media_state: str | None = None
    latency_ms: int | None = None
    error_type: str | None = None
    taxonomy_confidence: float | None = None
    message_redacted: str
    raw_message: str
    fingerprint: str | None = None
