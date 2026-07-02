from dataclasses import dataclass


@dataclass(frozen=True)
class Runbook:
    primary_root_cause: str
    recommended_fix: str
    verification_plan: tuple[str, ...]
    summary: str
    severity: str
    suspected_owner: str
    next_evidence_needed: tuple[str, ...]


RUNBOOKS: dict[str, Runbook] = {
    "PROVIDER_WEBHOOK_FAILED": Runbook(
        primary_root_cause="Telephony provider webhook failed before call lifecycle state could be updated.",
        recommended_fix="Inspect provider webhook delivery, authentication, response status, and call_sid mapping.",
        verification_plan=(
            "Replay a provider webhook payload in a test environment.",
            "Verify the endpoint returns a successful status code.",
            "Confirm call_sid or provider_call_id maps to an internal call record.",
        ),
        summary="Telephony provider webhook failed during call ingress or status update.",
        severity="high",
        suspected_owner="telephony_provider_integration",
        next_evidence_needed=(
            "provider.",
            "webhook payload id.",
            "HTTP status code.",
            "call_sid or provider_call_id.",
            "handler logs and response body.",
        ),
    ),
    "SIP_INVITE_FAILED": Runbook(
        primary_root_cause="SIP INVITE failed before the call could reach the media/session layer.",
        recommended_fix="Inspect SIP status code, trunk configuration, provider response, and INVITE routing.",
        verification_plan=(
            "Place a synthetic SIP call through the same trunk.",
            "Verify INVITE reaches the expected endpoint.",
            "Confirm provider status code and SIP Call-ID are captured.",
        ),
        summary="SIP INVITE failed before room/media setup.",
        severity="high",
        suspected_owner="sip_trunking",
        next_evidence_needed=(
            "SIP status code.",
            "trunk_id.",
            "provider response.",
            "sip_call_id.",
            "INVITE/ACK/BYE sequence.",
        ),
    ),
    "PARTICIPANT_JOIN_TIMEOUT": Runbook(
        primary_root_cause="Participant did not join the media room within the expected timeout.",
        recommended_fix="Inspect room_id, participant_identity, dispatch_id, media bridge state, and provider leg status.",
        verification_plan=(
            "Run synthetic call into a test room.",
            "Verify the participant joins within expected timeout.",
            "Check media bridge and LiveKit room lifecycle logs.",
        ),
        summary="Participant join timed out during session orchestration.",
        severity="high",
        suspected_owner="session_orchestrator",
        next_evidence_needed=(
            "room_id.",
            "participant_identity.",
            "dispatch_id.",
            "LiveKit room state.",
            "SIP call_sid.",
        ),
    ),
    "LLM_DEPLOYMENT_NOT_FOUND": Runbook(
        primary_root_cause="Configured LLM deployment was not found.",
        recommended_fix="Audit the LLM deployment name and environment configuration.",
        verification_plan=(
            "Confirm deployment exists in provider console.",
            "Run one test call through llm_node.",
            "Verify TTS is reached after LLM response.",
        ),
        summary="LLM provider rejected the configured deployment before response generation.",
        severity="high",
        suspected_owner="llm_provider_config",
        next_evidence_needed=(
            "LLM deployment name from runtime configuration.",
            "Provider request id or response body.",
            "Environment/config snapshot for the affected agent.",
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
        summary="Async runtime emitted an unsupervised task exception.",
        severity="medium",
        suspected_owner="runtime_platform",
        next_evidence_needed=(
            "Task creation site.",
            "Full traceback from the task body.",
            "Call or turn id associated with the task.",
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
        summary="LiveKit session lifecycle was closed before a later operation used it.",
        severity="high",
        suspected_owner="livekit_session_lifecycle",
        next_evidence_needed=(
            "Room id and session id.",
            "Session close timestamp.",
            "Operation attempted after close.",
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
        summary="Mock session API drifted from the production session interface.",
        severity="medium",
        suspected_owner="test_runtime",
        next_evidence_needed=(
            "MockSession.say signature.",
            "Production session.say signature.",
            "Call site passing allow_interruptions.",
        ),
    ),
    "STT_FAILURE_OR_LATENCY_SPIKE": Runbook(
        primary_root_cause="Speech-to-text processing failed or produced an empty transcript.",
        recommended_fix="Inspect STT provider, audio input quality, attempt count, and transcript output.",
        verification_plan=(
            "Replay a short known-good audio sample through stt_node.",
            "Verify transcript is produced within expected latency.",
            "Check provider attempt logs, audio duration, and error response.",
        ),
        summary="STT node failed or returned an empty transcript during call processing.",
        severity="high",
        suspected_owner="stt_pipeline",
        next_evidence_needed=(
            "stt_provider.",
            "audio_duration_ms.",
            "attempt_no.",
            "latency_ms.",
            "transcript content or empty indicator.",
        ),
    ),
    "TTS_FAILURE_OR_LATENCY_SPIKE": Runbook(
        primary_root_cause="Text-to-speech synthesis failed or playback did not start after synthesis.",
        recommended_fix="Inspect TTS provider, voice_id configuration, synthesis latency, and playback lifecycle events.",
        verification_plan=(
            "Run a known-good text response through tts_node.",
            "Verify synthesis completes within expected latency.",
            "Confirm playback_start and playback_end events are present in logs.",
        ),
        summary="TTS node failed to synthesize or deliver audio during call processing.",
        severity="high",
        suspected_owner="tts_pipeline",
        next_evidence_needed=(
            "tts_provider.",
            "voice_id.",
            "synthesis_latency_ms.",
            "playback_start and playback_end timestamps.",
            "provider error body.",
        ),
    ),
    "LIVEKIT_ROOM_CREATE_FAILED": Runbook(
        primary_root_cause="LiveKit room creation failed before the participant or agent could join.",
        recommended_fix="Inspect LiveKit server connectivity, room configuration, and API key credentials.",
        verification_plan=(
            "Attempt to create a test room using the same configuration.",
            "Verify LiveKit API key and server URL are reachable from the agent host.",
            "Check LiveKit server logs for room create rejection reason.",
        ),
        summary="LiveKit room creation failed before session could begin.",
        severity="high",
        suspected_owner="livekit_media_bridge",
        next_evidence_needed=(
            "LiveKit server URL and API key validity.",
            "room_id attempted.",
            "LiveKit server error response.",
            "Network connectivity between agent host and LiveKit server.",
        ),
    ),
    "AGENT_DISPATCH_FAILED": Runbook(
        primary_root_cause="Agent dispatch was created but the agent failed to join the room.",
        recommended_fix="Inspect dispatch_id, agent identity, room state, and whether the agent process started.",
        verification_plan=(
            "Replay a dispatch call into a test room.",
            "Verify the dispatch resolves and the agent joins within the expected timeout.",
            "Check LiveKit dispatch and agent process logs.",
        ),
        summary="Agent dispatch failed to complete during session orchestration.",
        severity="high",
        suspected_owner="session_orchestrator",
        next_evidence_needed=(
            "dispatch_id.",
            "room_id.",
            "agent_id.",
            "dispatch create timestamp and join timeout.",
            "LiveKit dispatch status response.",
        ),
    ),
    "SILENCE_MONITOR_FALSE_TRIGGER": Runbook(
        primary_root_cause="The silence monitor fired while TTS playback was active, incorrectly detecting silence.",
        recommended_fix="Audit silence threshold, monitor state synchronization with TTS playback lifecycle, and timer reset logic.",
        verification_plan=(
            "Reproduce by triggering a TTS response and observing silence monitor state.",
            "Verify the silence timer resets on playback_start.",
            "Confirm monitor state does not activate during active TTS.",
        ),
        summary="Silence monitor triggered during active TTS playback, indicating a false positive or state desync.",
        severity="medium",
        suspected_owner="monitor_pipeline",
        next_evidence_needed=(
            "Silence threshold configuration.",
            "TTS playback_start and playback_end timestamps.",
            "Monitor state transitions around the trigger time.",
            "call_sid and turn_id.",
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
    summary="No deterministic VoiceOps fingerprint matched the submitted logs.",
    severity="medium",
    suspected_owner="unknown",
    next_evidence_needed=(
        "Full structured logs for the affected call.",
        "Call id, room id, agent id, and turn id.",
        "Provider request ids and relevant config snapshot.",
    ),
)


UNKNOWN_PHASE_RUNBOOKS: dict[str, Runbook] = {
    "llm": Runbook(
        primary_root_cause="Unknown failure during LLM provider execution.",
        recommended_fix="Inspect provider, model or deployment, environment configuration, and provider error body.",
        verification_plan=(
            "Run one test call through llm_node.",
            "Verify the provider accepts the configured model or deployment.",
            "Confirm downstream TTS is reached after LLM response.",
        ),
        summary="Unknown failure appears to be in the LLM phase.",
        severity="medium",
        suspected_owner="llm_provider_config",
        next_evidence_needed=(
            "provider.",
            "model_or_deployment.",
            "env/config snapshot.",
            "request error body.",
        ),
    ),
    "sip": Runbook(
        primary_root_cause="Unknown failure during SIP signaling.",
        recommended_fix="Inspect SIP status, trunk configuration, provider response, and call signaling sequence.",
        verification_plan=(
            "Place a synthetic SIP call through the same trunk.",
            "Verify INVITE/ACK/BYE sequence is present.",
            "Confirm provider status code and call_sid are captured.",
        ),
        summary="Unknown failure appears to be in SIP or telephony signaling.",
        severity="medium",
        suspected_owner="telephony_provider",
        next_evidence_needed=(
            "SIP status code.",
            "trunk_id.",
            "provider response.",
            "call_sid.",
            "INVITE/ACK/BYE sequence.",
        ),
    ),
    "participant_join": Runbook(
        primary_root_cause="Unknown failure during LiveKit participant join.",
        recommended_fix="Inspect room_id, participant_identity, dispatch_id, and LiveKit room state.",
        verification_plan=(
            "Run synthetic SIP call into a test room.",
            "Verify participant joins within expected timeout.",
            "Check LiveKit dispatch and room lifecycle logs.",
        ),
        summary="Unknown failure occurred while a participant was joining a LiveKit room.",
        severity="medium",
        suspected_owner="livekit_entrypoint",
        next_evidence_needed=(
            "room_id and participant_identity.",
            "dispatch_id and room lifecycle logs.",
            "Join timeout and LiveKit server response.",
        ),
    ),
    "stt": Runbook(
        primary_root_cause="Unknown failure during speech-to-text processing.",
        recommended_fix="Inspect STT provider attempts, audio duration, latency, and transcript output.",
        verification_plan=(
            "Replay a short audio sample through stt_node.",
            "Verify transcript is produced within expected latency.",
            "Check provider attempt logs and error response.",
        ),
        summary="Unknown failure appears to be in the STT phase.",
        severity="medium",
        suspected_owner="stt_pipeline",
        next_evidence_needed=(
            "stt_provider.",
            "audio_duration_ms.",
            "attempt_no.",
            "latency_ms.",
            "transcript_length.",
        ),
    ),
    "tts": Runbook(
        primary_root_cause="Unknown failure during text-to-speech synthesis or playback.",
        recommended_fix="Inspect TTS provider, voice configuration, synthesis latency, and playback lifecycle.",
        verification_plan=(
            "Run one known-good text response through tts_node.",
            "Verify synthesis completes within expected latency.",
            "Confirm playback_start and playback_end are logged.",
        ),
        summary="Unknown failure appears to be in the TTS phase.",
        severity="medium",
        suspected_owner="tts_pipeline",
        next_evidence_needed=(
            "tts_provider.",
            "voice_id.",
            "synthesis_latency_ms.",
            "playback_start/end.",
        ),
    ),
    "tool": Runbook(
        primary_root_cause="Unknown failure during tool execution or metadata mutation.",
        recommended_fix="Inspect tool identity, argument schema, and call_metadata before/after diff.",
        verification_plan=(
            "Run the affected tool with the captured arguments.",
            "Verify output schema and metadata mutation are expected.",
            "Confirm downstream LLM/TTS path continues after tool completion.",
        ),
        summary="Unknown failure appears to be in a tool or metadata mutation path.",
        severity="medium",
        suspected_owner="function_tools",
        next_evidence_needed=(
            "tool_name.",
            "tool_class.",
            "args schema.",
            "call_metadata before/after diff.",
        ),
    ),
}
