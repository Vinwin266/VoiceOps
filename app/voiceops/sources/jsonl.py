import json
from pathlib import Path
from typing import Any

from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.events.normalizer import build_voiceops_event


def load_jsonl_events(path: str | Path, run_id: int | None = None) -> list[VoiceOpsEvent]:
    events: list[VoiceOpsEvent] = []

    with Path(path).open("r", encoding="utf-8") as file:
        for index, line in enumerate(file, start=1):
            if not line.strip():
                continue

            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL line {index} must be an object")

            events.append(_event_from_payload(payload=payload, run_id=run_id, index=index))

    return events


def parse_jsonl_events(raw_jsonl: str, run_id: int | None = None) -> list[VoiceOpsEvent]:
    events: list[VoiceOpsEvent] = []

    for index, line in enumerate(raw_jsonl.splitlines(), start=1):
        if not line.strip():
            continue

        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"JSONL line {index} must be an object")

        events.append(_event_from_payload(payload=payload, run_id=run_id, index=index))

    return events


def _event_from_payload(
    payload: dict[str, Any],
    run_id: int | None,
    index: int,
) -> VoiceOpsEvent:
    raw_message = payload.get("raw_message") or payload.get("message")
    if not isinstance(raw_message, str) or not raw_message.strip():
        raise ValueError(f"JSONL line {index} must include raw_message or message")

    event_run_id = payload.get("run_id", run_id)
    return build_voiceops_event(
        raw_message=raw_message,
        run_id=event_run_id,
        index=index,
        event_id=payload.get("event_id"),
        message_redacted=payload.get("message_redacted"),
        **{
            key: value
            for key, value in payload.items()
            if key
            not in {
                "event_id",
                "run_id",
                "raw_message",
                "message",
                "message_redacted",
            }
        },
    )
