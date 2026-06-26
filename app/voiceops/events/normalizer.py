import hashlib
import re
from typing import Any

from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.taxonomy import canonicalize_source_module, infer_event_taxonomy


def normalize_logs(raw_text: str, run_id: int | None = None) -> list[VoiceOpsEvent]:
    lines = [line.rstrip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        lines = [raw_text.strip()]

    event_messages = _group_multiline_events(lines)

    return [
        build_voiceops_event(run_id=run_id, index=index, raw_message=message)
        for index, message in enumerate(event_messages, start=1)
    ]


def build_voiceops_event(
    raw_message: str,
    run_id: int | None = None,
    index: int = 1,
    event_id: str | None = None,
    message_redacted: str | None = None,
    **fields: Any,
) -> VoiceOpsEvent:
    source_module = fields.get("source_module")
    source_module_value = str(source_module) if source_module is not None else None
    taxonomy = infer_event_taxonomy(raw_message)
    canonical_module = (
        fields.get("canonical_module")
        or canonicalize_source_module(source_module_value)
        or taxonomy.canonical_module
    )
    phase = fields.get("phase") or taxonomy.phase
    pipeline_node = fields.get("pipeline_node") or taxonomy.pipeline_node

    return VoiceOpsEvent(
        event_id=event_id or _event_id(run_id=run_id, index=index, message=raw_message),
        run_id=run_id,
        timestamp=fields.get("timestamp"),
        source_system=fields.get("source_system"),
        source_module=source_module_value,
        canonical_module=canonical_module,
        level=fields.get("level") or _infer_level(raw_message),
        module=canonical_module,
        phase=phase,
        pipeline_node=pipeline_node,
        call_sid=fields.get("call_sid"),
        provider_call_id=fields.get("provider_call_id"),
        sip_call_id=fields.get("sip_call_id"),
        room_id=fields.get("room_id"),
        agent_id=fields.get("agent_id"),
        participant_id=fields.get("participant_id"),
        turn_id=fields.get("turn_id"),
        provider=fields.get("provider"),
        protocol=fields.get("protocol"),
        direction=fields.get("direction"),
        from_number=fields.get("from_number"),
        to_number=fields.get("to_number"),
        status_code=fields.get("status_code"),
        hangup_cause=fields.get("hangup_cause"),
        media_state=fields.get("media_state"),
        latency_ms=fields.get("latency_ms"),
        taxonomy_confidence=taxonomy.confidence,
        error_type=fields.get("error_type") or _infer_error_type(raw_message),
        message_redacted=message_redacted or redact_message(raw_message),
        raw_message=raw_message,
        fingerprint=fields.get("fingerprint"),
    )


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
