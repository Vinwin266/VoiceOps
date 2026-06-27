import operator
from typing import Annotated, TypedDict

from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.fingerprints.matcher import FingerprintMatch
from app.voiceops.rca.report_builder import RCAReport


class RCAState(TypedDict, total=False):
    raw_input: str
    jsonl_input: str
    run_id: int
    events: list[VoiceOpsEvent]
    matches: list[FingerprintMatch]
    report: RCAReport
    errors: Annotated[list[str], operator.add]
