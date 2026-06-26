from dataclasses import dataclass


MODULES: tuple[str, ...] = (
    "telephony_provider",
    "call_routing",
    "sip",
    "pstn",
    "webhook",
    "media_bridge",
    "session_orchestrator",
    "voice_agent",
    "stt",
    "llm",
    "tool",
    "tts",
    "monitor",
    "teardown",
    "infra",
    "async_runtime",
    "unknown",
)

PHASES: tuple[str, ...] = (
    "inbound_call",
    "outbound_call",
    "provider_webhook",
    "sip_invite",
    "sip_registration",
    "call_routing",
    "number_mapping",
    "trunk_selection",
    "pstn_connect",
    "media_bridge",
    "room_create",
    "participant_join",
    "agent_dispatch",
    "session_start",
    "stt",
    "llm",
    "tool",
    "tts",
    "monitor",
    "transfer",
    "recording",
    "hangup",
    "teardown",
    "async_runtime",
    "unknown",
)

PIPELINE_NODES: tuple[str, ...] = (
    "entrypoint",
    "stt_node",
    "llm_node",
    "tool_node",
    "tts_node",
    "monitor",
    "dispatch",
    "unknown",
)

ERROR_FAMILIES: tuple[str, ...] = (
    "config",
    "provider",
    "lifecycle",
    "runtime",
    "test_runtime",
    "timeout",
    "unknown",
)


@dataclass(frozen=True)
class TaxonomyInference:
    phase: str = "unknown"
    module: str = "unknown"
    canonical_module: str = "unknown"
    pipeline_node: str | None = None
    confidence: float = 0.0
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class PhaseInferenceRule:
    phase: str
    module: str
    required_terms: tuple[str, ...]
    optional_terms: tuple[str, ...] = ()
    pipeline_node: str | None = None
    confidence: float = 0.45


PHASE_INFERENCE_RULES: tuple[PhaseInferenceRule, ...] = (
    PhaseInferenceRule(
        phase="llm",
        module="llm",
        pipeline_node="llm_node",
        required_terms=("DeploymentNotFound", "chat.completions", "llm_node", "llm"),
        optional_terms=("model", "deployment", "azure", "provider"),
        confidence=0.55,
    ),
    PhaseInferenceRule(
        phase="provider_webhook",
        module="webhook",
        required_terms=("webhook", "callback"),
        optional_terms=("twilio", "exotel", "provider", "call_sid", "status_code"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="sip_invite",
        module="sip",
        required_terms=("SIP", "INVITE"),
        optional_terms=("trunk", "call_sid", "ACK", "BYE"),
        confidence=0.5,
    ),
    PhaseInferenceRule(
        phase="sip_registration",
        module="sip",
        required_terms=("SIP", "REGISTER"),
        optional_terms=("trunk", "auth", "realm", "provider"),
        confidence=0.5,
    ),
    PhaseInferenceRule(
        phase="pstn_connect",
        module="pstn",
        required_terms=("PSTN", "connect"),
        optional_terms=("provider", "call_sid", "status_code"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="media_bridge",
        module="media_bridge",
        required_terms=("media", "bridge"),
        optional_terms=("room", "rtp", "livekit", "audio"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="room_create",
        module="media_bridge",
        required_terms=("room_create", "create room", "room created", "room creation"),
        optional_terms=("livekit", "room_id"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="participant_join",
        module="session_orchestrator",
        pipeline_node="entrypoint",
        required_terms=(
            "participant join",
            "join room",
            "participant failed to join",
            "participant waiting to join",
        ),
        optional_terms=("room", "timeout", "identity"),
        confidence=0.3,
    ),
    PhaseInferenceRule(
        phase="agent_dispatch",
        module="session_orchestrator",
        pipeline_node="dispatch",
        required_terms=("agent_dispatch", "create_dispatch", "dispatch"),
        optional_terms=("room", "agent", "livekit"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="stt",
        module="stt",
        pipeline_node="stt_node",
        required_terms=("transcript", "stt", "speech-to-text"),
        optional_terms=("audio", "latency", "provider"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="tts",
        module="tts",
        pipeline_node="tts_node",
        required_terms=("tts", "synthesis", "voice_id"),
        optional_terms=("playback", "latency", "provider"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="monitor",
        module="monitor",
        pipeline_node="monitor",
        required_terms=("silence", "prompt", "threshold"),
        optional_terms=("monitor", "timer", "state"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="tool",
        module="tool",
        pipeline_node="tool_node",
        required_terms=("call_metadata", "tool_name"),
        optional_terms=("tool", "metadata", "diff"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="async_runtime",
        module="async_runtime",
        required_terms=("Task exception", "asyncio", "never retrieved"),
        optional_terms=("task", "exception"),
        confidence=0.5,
    ),
)


SOURCE_MODULE_MAP: dict[str, str] = {
    "v1_entrypoint": "session_orchestrator",
    "v1_agent": "voice_agent",
    "v1_stt": "stt",
    "v1_tts": "tts",
    "v1_monitor": "monitor",
    "v1_function_tools.py": "tool",
    "twilio": "telephony_provider",
    "exotel": "telephony_provider",
    "freeswitch": "sip",
    "livekit": "media_bridge",
}


def canonicalize_source_module(source_module: str | None) -> str | None:
    if source_module is None:
        return None

    lowered = source_module.lower()
    for source_term, canonical_module in SOURCE_MODULE_MAP.items():
        if source_term.lower() in lowered:
            return canonical_module

    return None


def infer_event_taxonomy(message: str) -> TaxonomyInference:
    lowered = message.lower()
    best_inference = TaxonomyInference()

    for rule in PHASE_INFERENCE_RULES:
        matched_required_terms = tuple(
            term
            for term in rule.required_terms
            if term.lower() in lowered
        )
        if not matched_required_terms:
            continue

        matched_optional_terms = tuple(
            term
            for term in rule.optional_terms
            if term.lower() in lowered
        )
        matched_terms = matched_required_terms + matched_optional_terms
        confidence = round(
            min(
                0.8,
                rule.confidence
                + (len(matched_required_terms) - 1) * 0.05
                + len(matched_optional_terms) * 0.05,
            ),
            2,
        )
        if confidence <= best_inference.confidence:
            continue

        best_inference = TaxonomyInference(
            phase=rule.phase,
            module=rule.module,
            canonical_module=rule.module,
            pipeline_node=rule.pipeline_node,
            confidence=confidence,
            matched_terms=matched_terms,
        )

    return best_inference
