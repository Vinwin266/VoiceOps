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
)
