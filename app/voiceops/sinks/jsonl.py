import os
from pathlib import Path

from app.voiceops.events.model import VoiceOpsEvent


DEFAULT_JSONL_PATH = "/tmp/voiceops/events.jsonl"
JSONL_PATH_ENV = "VOICEOPS_JSONL_PATH"


def append_event(event: VoiceOpsEvent, path: str | Path | None = None) -> Path:
    sink_path = _resolve_path(path)
    sink_path.parent.mkdir(parents=True, exist_ok=True)

    with sink_path.open("a", encoding="utf-8") as file:
        file.write(event.model_dump_json(exclude_none=True))
        file.write("\n")

    return sink_path


def append_events(events: list[VoiceOpsEvent], path: str | Path | None = None) -> Path:
    sink_path = _resolve_path(path)
    sink_path.parent.mkdir(parents=True, exist_ok=True)

    with sink_path.open("a", encoding="utf-8") as file:
        for event in events:
            file.write(event.model_dump_json(exclude_none=True))
            file.write("\n")

    return sink_path


def _resolve_path(path: str | Path | None) -> Path:
    return Path(path or os.getenv(JSONL_PATH_ENV, DEFAULT_JSONL_PATH))
