from collections.abc import Iterable

from pydantic import BaseModel, Field

from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.fingerprints.matcher import FingerprintMatch
from app.voiceops.rca.runbooks import RUNBOOKS, UNKNOWN_RUNBOOK


class RCAReport(BaseModel):
    status: str = "rca_completed"
    primary_fingerprint: str
    phase: str
    module: str
    confidence: float
    primary_root_cause: str
    evidence: list[str]
    recommended_fix: str
    verification_plan: list[str]
    matched_fingerprints: list[str] = Field(default_factory=list)


def build_rca_report(
    events: list[VoiceOpsEvent],
    matches: list[FingerprintMatch],
) -> RCAReport:
    if not matches:
        return _build_unknown_report(events)

    primary = max(matches, key=lambda match: match.confidence)
    runbook = RUNBOOKS[primary.fingerprint]
    evidence = _unique(
        match.evidence
        for match in matches
        if match.fingerprint == primary.fingerprint
    )
    matched_fingerprints = _unique(
        match.fingerprint
        for match in matches
        if match.fingerprint != primary.fingerprint
    )

    return RCAReport(
        primary_fingerprint=primary.fingerprint,
        phase=primary.phase,
        module=primary.module,
        confidence=primary.confidence,
        primary_root_cause=runbook.primary_root_cause,
        evidence=evidence,
        recommended_fix=runbook.recommended_fix,
        verification_plan=list(runbook.verification_plan),
        matched_fingerprints=matched_fingerprints,
    )


def _build_unknown_report(events: list[VoiceOpsEvent]) -> RCAReport:
    evidence = [
        event.message_redacted[:240]
        for event in events
        if event.message_redacted
    ][:3]

    if not evidence:
        evidence = ["No non-empty log lines were provided."]

    return RCAReport(
        primary_fingerprint="UNKNOWN_VOICEOPS_FAILURE",
        phase="unknown",
        module="unknown",
        confidence=0.2,
        primary_root_cause=UNKNOWN_RUNBOOK.primary_root_cause,
        evidence=evidence,
        recommended_fix=UNKNOWN_RUNBOOK.recommended_fix,
        verification_plan=list(UNKNOWN_RUNBOOK.verification_plan),
        matched_fingerprints=[],
    )


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)

    return unique_values
