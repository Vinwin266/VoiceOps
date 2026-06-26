from dataclasses import dataclass


MODULES: tuple[str, ...] = (
    "v1_entrypoint",
    "v1_agent",
    "v1_stt",
    "v1_tts",
    "v1_monitor",
    "v1_function_tools.py",
    "livekit",
    "llm_provider",
    "telephony_provider",
    "async_runtime",
    "unknown",
)

PHASES: tuple[str, ...] = (
    "telephony",
    "sip",
    "room_create",
    "participant_join",
    "dispatch",
    "session_start",
    "stt",
    "llm",
    "tool",
    "tts",
    "monitor",
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
        module="llm_provider",
        pipeline_node="llm_node",
        required_terms=("DeploymentNotFound", "chat.completions", "llm_node", "llm"),
        optional_terms=("model", "deployment", "azure", "provider"),
        confidence=0.55,
    ),
    PhaseInferenceRule(
        phase="sip",
        module="telephony_provider",
        required_terms=("SIP", "INVITE"),
        optional_terms=("trunk", "call_sid", "ACK", "BYE"),
        confidence=0.5,
    ),
    PhaseInferenceRule(
        phase="participant_join",
        module="v1_entrypoint",
        pipeline_node="entrypoint",
        required_terms=("participant", "join"),
        optional_terms=("room", "timeout", "identity"),
        confidence=0.3,
    ),
    PhaseInferenceRule(
        phase="dispatch",
        module="livekit",
        pipeline_node="dispatch",
        required_terms=("agent_dispatch", "create_dispatch", "dispatch"),
        optional_terms=("room", "agent", "livekit"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="stt",
        module="v1_stt",
        pipeline_node="stt_node",
        required_terms=("transcript", "stt", "speech-to-text"),
        optional_terms=("audio", "latency", "provider"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="tts",
        module="v1_tts",
        pipeline_node="tts_node",
        required_terms=("tts", "synthesis", "voice_id"),
        optional_terms=("playback", "latency", "provider"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="monitor",
        module="v1_monitor",
        pipeline_node="monitor",
        required_terms=("silence", "prompt", "threshold"),
        optional_terms=("monitor", "timer", "state"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="tool",
        module="v1_function_tools.py",
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
            pipeline_node=rule.pipeline_node,
            confidence=confidence,
            matched_terms=matched_terms,
        )

    return best_inference
