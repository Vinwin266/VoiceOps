import hashlib
import re

from app.voiceops.events.model import VoiceOpsEvent


def normalize_logs(raw_text: str, run_id: int | None = None) -> list[VoiceOpsEvent]:
    lines = [line.rstrip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        lines = [raw_text.strip()]

    event_messages = _group_multiline_events(lines)

    return [
        VoiceOpsEvent(
            event_id=_event_id(run_id=run_id, index=index, message=message),
            run_id=run_id,
            level=_infer_level(message),
            error_type=_infer_error_type(message),
            message_redacted=redact_message(message),
            raw_message=message,
        )
        for index, message in enumerate(event_messages, start=1)
    ]


def _group_multiline_events(lines: list[str]) -> list[str]:
    events: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if _starts_traceback_with_prefix(lines, index):
            block, index = _consume_traceback(lines, index + 1, prefix=line.strip())
            events.append(block)
            continue

        if _is_traceback_start(line):
            block, index = _consume_traceback(lines, index)
            events.append(block)
            continue

        events.append(line.strip())
        index += 1

    return events


def _starts_traceback_with_prefix(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return _looks_like_error_prefix(lines[index]) and _is_traceback_start(lines[index + 1])


def _consume_traceback(
    lines: list[str],
    start_index: int,
    prefix: str | None = None,
) -> tuple[str, int]:
    block: list[str] = []
    if prefix is not None:
        block.append(prefix)

    index = start_index
    block.append(lines[index])
    index += 1

    while index < len(lines) and not _starts_new_log_record(lines[index]):
        block.append(lines[index])
        index += 1

    return "\n".join(block).strip(), index


def _is_traceback_start(line: str) -> bool:
    return line.lstrip().startswith("Traceback ")


def _looks_like_error_prefix(line: str) -> bool:
    return bool(re.match(r"^\s*(ERROR|CRITICAL)\b", line, re.IGNORECASE))


def _starts_new_log_record(line: str) -> bool:
    stripped = line.lstrip()
    return bool(
        re.match(
            r"^(\d{4}-\d{2}-\d{2}[T\s].*?\b)?(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL)\b",
            stripped,
            re.IGNORECASE,
        )
    )


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
