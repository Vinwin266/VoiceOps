from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.fingerprints.matcher import match_fingerprints
from app.voiceops.rca.report_builder import RCAReport, build_rca_report
from app.voiceops.sources.jsonl import parse_jsonl_events
from app.voiceops.sources.raw_text import load_raw_text_events


def analyze_events(events: list[VoiceOpsEvent]) -> RCAReport:
    matches = match_fingerprints(events)
    return build_rca_report(events=events, matches=matches)


def analyze_raw_text(raw_text: str, run_id: int | None = None) -> RCAReport:
    return analyze_events(load_raw_text_events(raw_text=raw_text, run_id=run_id))


def analyze_jsonl(raw_jsonl: str, run_id: int | None = None) -> RCAReport:
    return analyze_events(parse_jsonl_events(raw_jsonl=raw_jsonl, run_id=run_id))
