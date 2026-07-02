from dataclasses import dataclass


@dataclass(frozen=True)
class MatchPattern:
    value: str
    is_regex: bool = False


@dataclass(frozen=True)
class FingerprintRule:
    fingerprint: str
    patterns: tuple[MatchPattern, ...]
    required_terms: tuple[str, ...]
    phase: str
    module: str
    confidence: float
    runbook_key: str


KNOWN_FINGERPRINT_RULES: tuple[FingerprintRule, ...] = (
    FingerprintRule(
        fingerprint="PROVIDER_WEBHOOK_FAILED",
        patterns=(
            MatchPattern("provider webhook failed"),
            MatchPattern("webhook failed"),
            MatchPattern(r"(twilio|exotel|provider).*webhook.*(failed|error)", is_regex=True),
        ),
        required_terms=("webhook",),
        phase="provider_webhook",
        module="telephony_provider",
        confidence=0.9,
        runbook_key="PROVIDER_WEBHOOK_FAILED",
    ),
    FingerprintRule(
        fingerprint="SIP_INVITE_FAILED",
        patterns=(
            MatchPattern("SIP INVITE failed"),
            MatchPattern(r"INVITE.*(failed|4\d\d|5\d\d|timeout)", is_regex=True),
        ),
        required_terms=("SIP", "INVITE"),
        phase="sip_invite",
        module="sip",
        confidence=0.9,
        runbook_key="SIP_INVITE_FAILED",
    ),
    FingerprintRule(
        fingerprint="PARTICIPANT_JOIN_TIMEOUT",
        patterns=(
            MatchPattern("participant failed to join"),
            MatchPattern("participant join timeout"),
            MatchPattern(r"participant.*join.*(timeout|timed out|failed)", is_regex=True),
        ),
        required_terms=("participant", "join"),
        phase="participant_join",
        module="session_orchestrator",
        confidence=0.9,
        runbook_key="PARTICIPANT_JOIN_TIMEOUT",
    ),
    FingerprintRule(
        fingerprint="LLM_DEPLOYMENT_NOT_FOUND",
        patterns=(
            MatchPattern("DeploymentNotFound"),
            MatchPattern(r"Error code:\s*404.*DeploymentNotFound", is_regex=True),
            MatchPattern("chat.completions.create"),
        ),
        required_terms=("DeploymentNotFound",),
        phase="llm",
        module="v1_agent / llm_node",
        confidence=0.95,
        runbook_key="LLM_DEPLOYMENT_NOT_FOUND",
    ),
    FingerprintRule(
        fingerprint="UNOBSERVED_ASYNC_TASK_EXCEPTION",
        patterns=(
            MatchPattern("Task exception was never retrieved"),
            MatchPattern(r"Task exception.*never retrieved", is_regex=True),
        ),
        required_terms=("Task exception", "never retrieved"),
        phase="async_runtime",
        module="asyncio task supervisor",
        confidence=0.9,
        runbook_key="UNOBSERVED_ASYNC_TASK_EXCEPTION",
    ),
    FingerprintRule(
        fingerprint="LIVEKIT_SESSION_CLOSED",
        patterns=(
            MatchPattern("Session is closed"),
            MatchPattern(r"(LiveKit|session).*closed", is_regex=True),
        ),
        required_terms=("Session", "closed"),
        phase="dispatch/session_lifecycle",
        module="LiveKit dispatch/session lifecycle",
        confidence=0.9,
        runbook_key="LIVEKIT_SESSION_CLOSED",
    ),
    FingerprintRule(
        fingerprint="SESSION_SAY_SIGNATURE_MISMATCH",
        patterns=(
            MatchPattern("MockSession.say unexpected keyword allow_interruptions"),
            MatchPattern(
                r"MockSession\.say.*unexpected keyword.*allow_interruptions",
                is_regex=True,
            ),
        ),
        required_terms=("MockSession.say", "allow_interruptions"),
        phase="tool/test_runtime",
        module="session protocol/mock parity",
        confidence=0.9,
        runbook_key="SESSION_SAY_SIGNATURE_MISMATCH",
    ),
    FingerprintRule(
        fingerprint="STT_FAILURE_OR_LATENCY_SPIKE",
        patterns=(
            MatchPattern("stt failed"),
            MatchPattern("transcript is empty"),
            MatchPattern("speech recognition failed"),
            MatchPattern(r"stt.*(failed|error|timeout|latency)", is_regex=True),
            MatchPattern(r"transcript.*(empty|none|missing)", is_regex=True),
        ),
        required_terms=("stt",),
        phase="stt",
        module="stt",
        confidence=0.9,
        runbook_key="STT_FAILURE_OR_LATENCY_SPIKE",
    ),
    FingerprintRule(
        fingerprint="TTS_FAILURE_OR_LATENCY_SPIKE",
        patterns=(
            MatchPattern("tts failed"),
            MatchPattern("synthesis failed"),
            MatchPattern("playback did not start"),
            MatchPattern(r"tts.*(failed|error|timeout|latency)", is_regex=True),
            MatchPattern(r"synthesis.*(failed|error|timeout)", is_regex=True),
        ),
        required_terms=("tts",),
        phase="tts",
        module="tts",
        confidence=0.9,
        runbook_key="TTS_FAILURE_OR_LATENCY_SPIKE",
    ),
    FingerprintRule(
        fingerprint="LIVEKIT_ROOM_CREATE_FAILED",
        patterns=(
            MatchPattern("room creation failed"),
            MatchPattern("failed to create room"),
            MatchPattern(r"room.*(create|creation).*(failed|error)", is_regex=True),
        ),
        required_terms=("room",),
        phase="room_create",
        module="media_bridge",
        confidence=0.9,
        runbook_key="LIVEKIT_ROOM_CREATE_FAILED",
    ),
    FingerprintRule(
        fingerprint="AGENT_DISPATCH_FAILED",
        patterns=(
            MatchPattern("agent dispatch failed"),
            MatchPattern("dispatch failed"),
            MatchPattern("create_dispatch failed"),
            MatchPattern(r"(agent_dispatch|create_dispatch).*(failed|error|timeout)", is_regex=True),
        ),
        required_terms=("dispatch",),
        phase="agent_dispatch",
        module="session_orchestrator",
        confidence=0.9,
        runbook_key="AGENT_DISPATCH_FAILED",
    ),
    FingerprintRule(
        fingerprint="SILENCE_MONITOR_FALSE_TRIGGER",
        patterns=(
            MatchPattern("silence monitor triggered"),
            MatchPattern("silence detected during tts"),
            MatchPattern("silence threshold exceeded"),
            MatchPattern(r"silence.*(monitor|trigger|threshold).*(tts|playback|active)", is_regex=True),
            MatchPattern(r"monitor.*(silence|trigger).*(active|tts|playback)", is_regex=True),
        ),
        required_terms=("silence",),
        phase="monitor",
        module="monitor",
        confidence=0.9,
        runbook_key="SILENCE_MONITOR_FALSE_TRIGGER",
    ),
)
