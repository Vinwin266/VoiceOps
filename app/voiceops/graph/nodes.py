from app.voiceops.fingerprints.matcher import match_fingerprints
from app.voiceops.graph.state import RCAState
from app.voiceops.rca.report_builder import build_rca_report
from app.voiceops.sources.jsonl import parse_jsonl_events
from app.voiceops.sources.raw_text import load_raw_text_events


def load_input(state: RCAState) -> RCAState:
    run_id = state.get("run_id")

    if "events" in state:
        return {}

    if jsonl_input := state.get("jsonl_input"):
        return {"events": parse_jsonl_events(jsonl_input, run_id=run_id)}

    if raw_input := state.get("raw_input"):
        return {"events": load_raw_text_events(raw_text=raw_input, run_id=run_id)}

    return {"events": [], "errors": ["raw_input, jsonl_input, or events is required"]}


def match_known_fingerprints(state: RCAState) -> RCAState:
    return {"matches": match_fingerprints(state.get("events", []))}


def build_report(state: RCAState) -> RCAState:
    return {
        "report": build_rca_report(
            events=state.get("events", []),
            matches=state.get("matches", []),
        )
    }
