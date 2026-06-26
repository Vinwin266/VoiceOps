import hashlib
import re

from app.voiceops.events.model import VoiceOpsEvent


def normalize_logs(raw_text: str, run_id: int | None = None) -> list[VoiceOpsEvent]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    lines =[line.strip() for line in raw_text.split('\n') if line.strip()]
    if not lines:
        lines = [raw_text.strip()]

    return [
        VoiceOpsEvent(
            event_id=_event_id(run_id=run_id, index=index, message=line),
            run_id=run_id,
            level=_infer_level(line),
            error_type=_infer_error_type(line),
            message_redacted=redact_message(line),
            raw_message=line,
        )
        for index, line in enumerate(lines, start=1)
    ]


def redact_message(message: str) -> str:
    redacted = re.sub(r"\b[\w.+-]+@[\w.-]+\.\w+\b", "[email]", message)
    redacted = re.sub(
        r"(?i)\b(bearer|api[_-]?key|token|secret)\s*[:=]\s*\S+",
        r"\1=[redacted]",
        redacted,
    )
    return redacted


def _event_id(run_id: int | None, index: int, message: str) -> str:
    stable_input = f"{run_id or 'none'}:{index}:{message}".encode("utf-8")
    return f"evt_{hashlib.sha1(stable_input).hexdigest()[:16]}"


def _infer_level(message: str) -> str:
    lowered = message.lower()
    if "traceback" in lowered or "exception" in lowered or "error" in lowered:
        return "error"
    if "warn" in lowered:
        return "warning"
    if "debug" in lowered:
        return "debug"
    if "info" in lowered:
        return "info"
    return "unknown"


def _infer_error_type(message: str) -> str | None:
    lowered = message.lower()
    if "exception" in lowered:
        return "exception"
    if "error" in lowered:
        return "error"
    return None
