from dataclasses import dataclass


@dataclass(frozen=True)
class Runbook:
    primary_root_cause: str
    recommended_fix: str
    verification_plan: tuple[str, ...]


RUNBOOKS: dict[str, Runbook] = {
    "LLM_DEPLOYMENT_NOT_FOUND": Runbook(
        primary_root_cause="Configured LLM deployment was not found.",
        recommended_fix="Audit the LLM deployment name and environment configuration.",
        verification_plan=(
            "Confirm deployment exists in provider console.",
            "Run one test call through llm_node.",
            "Verify TTS is reached after LLM response.",
        ),
    ),
    "UNOBSERVED_ASYNC_TASK_EXCEPTION": Runbook(
        primary_root_cause="An async task raised an exception without being awaited or supervised.",
        recommended_fix="Wrap background task creation with a safe_create_task helper that logs and handles task failures.",
        verification_plan=(
            "Reproduce the failing path with task supervision enabled.",
            "Confirm the exception is attached to the originating call or turn.",
            "Verify no 'Task exception was never retrieved' message appears in logs.",
        ),
    ),
    "LIVEKIT_SESSION_CLOSED": Runbook(
        primary_root_cause="The LiveKit session was used after its lifecycle had already closed.",
        recommended_fix="Audit LiveKit client/session ownership and guard dispatch or playback calls after close.",
        verification_plan=(
            "Run a call through normal connect and disconnect.",
            "Trigger the failing dispatch path after disconnect.",
            "Verify closed sessions are skipped or recreated before use.",
        ),
    ),
    "SESSION_SAY_SIGNATURE_MISMATCH": Runbook(
        primary_root_cause="The test/mock session interface does not match the production session.say signature.",
        recommended_fix="Update MockSession.say to accept allow_interruptions or align calls to the shared session protocol.",
        verification_plan=(
            "Run the affected tool or test path with MockSession.",
            "Verify allow_interruptions is accepted or removed consistently.",
            "Add a protocol/interface test to prevent future mock drift.",
        ),
    ),
}


UNKNOWN_RUNBOOK = Runbook(
    primary_root_cause="No known VoiceOps fingerprint matched the submitted logs.",
    recommended_fix="Review the evidence manually, then add a deterministic fingerprint when the root cause is confirmed.",
    verification_plan=(
        "Reproduce the failure with structured logs enabled.",
        "Identify the failing voice pipeline phase.",
        "Add a targeted fingerprint and runbook once confirmed.",
    ),
)
