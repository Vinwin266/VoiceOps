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
    terms: tuple[str, ...]
    pipeline_node: str | None = None
    confidence: float = 0.45


PHASE_INFERENCE_RULES: tuple[PhaseInferenceRule, ...] = (
    PhaseInferenceRule(
        phase="llm",
        module="llm_provider",
        pipeline_node="llm_node",
        terms=("DeploymentNotFound", "chat.completions", "llm", "model"),
        confidence=0.55,
    ),
    PhaseInferenceRule(
        phase="sip",
        module="telephony_provider",
        terms=("SIP", "INVITE", "trunk"),
        confidence=0.5,
    ),
    PhaseInferenceRule(
        phase="participant_join",
        module="v1_entrypoint",
        pipeline_node="entrypoint",
        terms=("participant", "join", "room"),
        confidence=0.35,
    ),
    PhaseInferenceRule(
        phase="dispatch",
        module="livekit",
        pipeline_node="dispatch",
        terms=("agent_dispatch", "create_dispatch", "dispatch"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="stt",
        module="v1_stt",
        pipeline_node="stt_node",
        terms=("transcript", "stt", "speech-to-text"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="tts",
        module="v1_tts",
        pipeline_node="tts_node",
        terms=("tts", "synthesis", "voice_id"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="monitor",
        module="v1_monitor",
        pipeline_node="monitor",
        terms=("silence", "prompt", "threshold"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="tool",
        module="v1_function_tools.py",
        pipeline_node="tool_node",
        terms=("call_metadata", "tool_name"),
        confidence=0.45,
    ),
    PhaseInferenceRule(
        phase="async_runtime",
        module="async_runtime",
        terms=("Task exception", "asyncio", "never retrieved"),
        confidence=0.5,
    ),
)


def infer_event_taxonomy(message: str) -> TaxonomyInference:
    lowered = message.lower()
    best_inference = TaxonomyInference()

    for rule in PHASE_INFERENCE_RULES:
        matched_terms = tuple(
            term
            for term in rule.terms
            if term.lower() in lowered
        )
        if not matched_terms:
            continue

        confidence = round(
            min(0.8, rule.confidence + (len(matched_terms) - 1) * 0.05),
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
