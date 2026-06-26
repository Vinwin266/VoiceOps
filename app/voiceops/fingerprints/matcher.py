from dataclasses import dataclass

from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.fingerprints.rules import (
    KNOWN_FINGERPRINT_RULES,
    FingerprintRule,
)


@dataclass(frozen=True)
class FingerprintMatch:
    fingerprint: str
    phase: str
    module: str
    confidence: float
    evidence: str
    event_id: str


def match_fingerprints(
    events: list[VoiceOpsEvent],
    rules: tuple[FingerprintRule, ...] = KNOWN_FINGERPRINT_RULES,
) -> list[FingerprintMatch]:
    matches: list[FingerprintMatch] = []

    for event in events:
        haystack = event.raw_message.lower()
        for rule in rules:
            if rule.match_text.lower() in haystack:
                matches.append(
                    FingerprintMatch(
                        fingerprint=rule.fingerprint,
                        phase=rule.phase,
                        module=rule.module,
                        confidence=rule.confidence,
                        evidence=rule.match_text,
                        event_id=event.event_id,
                    )
                )

    return matches
