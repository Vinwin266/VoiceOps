from dataclasses import dataclass


@dataclass(frozen=True)
class FingerprintRule:
    fingerprint: str
    match_text: str
    phase: str
    module: str
    confidence: float


KNOWN_FINGERPRINT_RULES: tuple[FingerprintRule, ...] = (
    FingerprintRule(
        fingerprint="LLM_DEPLOYMENT_NOT_FOUND",
        match_text="DeploymentNotFound",
        phase="llm",
        module="v1_agent / llm_node",
        confidence=0.95,
    ),
    FingerprintRule(
        fingerprint="UNOBSERVED_ASYNC_TASK_EXCEPTION",
        match_text="Task exception was never retrieved",
        phase="async_runtime",
        module="asyncio task supervisor",
        confidence=0.9,
    ),
    FingerprintRule(
        fingerprint="LIVEKIT_SESSION_CLOSED",
        match_text="Session is closed",
        phase="dispatch/session_lifecycle",
        module="LiveKit dispatch/session lifecycle",
        confidence=0.9,
    ),
    FingerprintRule(
        fingerprint="SESSION_SAY_SIGNATURE_MISMATCH",
        match_text="MockSession.say unexpected keyword allow_interruptions",
        phase="tool/test_runtime",
        module="session protocol/mock parity",
        confidence=0.9,
    ),
)
