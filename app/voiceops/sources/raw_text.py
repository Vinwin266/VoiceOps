from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.events.normalizer import normalize_logs


def load_raw_text_events(raw_text: str, run_id: int | None = None) -> list[VoiceOpsEvent]:
    return normalize_logs(raw_text=raw_text, run_id=run_id)
