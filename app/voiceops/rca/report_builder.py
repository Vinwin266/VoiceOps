from collections.abc import Iterable

from pydantic import BaseModel, Field

from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.fingerprints.matcher import FingerprintMatch
from app.voiceops.rca.runbooks import (
    RUNBOOKS,
    UNKNOWN_PHASE_RUNBOOKS,
    UNKNOWN_RUNBOOK,
)


class RCAReport(BaseModel):
    status: str = "rca_completed"
    primary_fingerprint: str
    phase: str
    module: str
    severity: str
    summary: str
    confidence: float
    primary_root_cause: str
    evidence: list[str]
    recommended_fix: str
    verification_plan: list[str]
    suspected_owner: str
    next_evidence_needed: list[str]
    event_count: int
    matched_event_ids: list[str]
    matched_fingerprints: list[str] = Field(default_factory=list)


def build_rca_report(
    events: list[VoiceOpsEvent],
    matches: list[FingerprintMatch],
) -> RCAReport:
    if not matches:
        return _build_unknown_report(events)

    primary = max(matches, key=lambda match: match.confidence)
    runbook = RUNBOOKS[primary.runbook_key]
    evidence = _unique(
        match.evidence
        for match in matches
        if match.fingerprint == primary.fingerprint
    )
    matched_event_ids = _unique(match.event_id for match in matches)
    matched_fingerprints = _unique(
        match.fingerprint
        for match in matches
        if match.fingerprint != primary.fingerprint
    )

    return RCAReport(
        primary_fingerprint=primary.fingerprint,
        phase=primary.phase,
        module=primary.module,
        severity=runbook.severity,
        summary=runbook.summary,
        confidence=primary.confidence,
        primary_root_cause=runbook.primary_root_cause,
        evidence=evidence,
        recommended_fix=runbook.recommended_fix,
        verification_plan=list(runbook.verification_plan),
        suspected_owner=runbook.suspected_owner,
        next_evidence_needed=list(runbook.next_evidence_needed),
        event_count=len(events),
        matched_event_ids=matched_event_ids,
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

    classified_event = _best_classified_event(events)
    phase = (
        classified_event.phase
        if classified_event is not None and classified_event.phase is not None
        else "unknown"
    )
    module = (
        classified_event.module
        if classified_event is not None and classified_event.module is not None
        else "unknown"
    )
    confidence = (
        classified_event.taxonomy_confidence
        if classified_event is not None and classified_event.taxonomy_confidence is not None
        else 0.2
    )
    runbook = UNKNOWN_PHASE_RUNBOOKS.get(phase, UNKNOWN_RUNBOOK)

    return RCAReport(
        primary_fingerprint="UNKNOWN_VOICEOPS_FAILURE",
        phase=phase,
        module=module,
        severity=runbook.severity,
        summary=runbook.summary,
        confidence=confidence,
        primary_root_cause=runbook.primary_root_cause,
        evidence=evidence,
        recommended_fix=runbook.recommended_fix,
        verification_plan=list(runbook.verification_plan),
        suspected_owner=runbook.suspected_owner,
        next_evidence_needed=list(runbook.next_evidence_needed),
        event_count=len(events),
        matched_event_ids=[],
        matched_fingerprints=[],
    )


def _best_classified_event(events: list[VoiceOpsEvent]) -> VoiceOpsEvent | None:
    classified_events = [
        event
        for event in events
        if event.phase not in (None, "unknown")
        and event.module not in (None, "unknown")
        and event.taxonomy_confidence is not None
    ]
    if not classified_events:
        return None
    return max(classified_events, key=lambda event: event.taxonomy_confidence or 0.0)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)

    return unique_values
