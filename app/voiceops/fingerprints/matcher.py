from dataclasses import dataclass
import re

from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.fingerprints.rules import (
    KNOWN_FINGERPRINT_RULES,
    FingerprintRule,
    MatchPattern,
)


@dataclass(frozen=True)
class FingerprintMatch:
    fingerprint: str
    runbook_key: str
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
        haystack = event.raw_message
        for rule in rules:
            if _matches_rule(rule=rule, haystack=haystack):
                matches.append(
                    FingerprintMatch(
                        fingerprint=rule.fingerprint,
                        runbook_key=rule.runbook_key,
                        phase=rule.phase,
                        module=rule.module,
                        confidence=rule.confidence,
                        evidence=_extract_evidence(
                            redacted_message=event.message_redacted,
                            rule=rule,
                        ),
                        event_id=event.event_id,
                    )
                )

    return matches

"""_matches_rule checks if the rule matches the haystack.
"""
def _matches_rule(rule: FingerprintRule, haystack: str) -> bool:
    lowered = haystack.lower()
    if not all(term.lower() in lowered for term in rule.required_terms):
        return False

    return any(_matches_pattern(pattern, haystack) for pattern in rule.patterns)

"""
_matches_pattern checks if the pattern matches the haystack.
"""
def _matches_pattern(pattern: MatchPattern, haystack: str) -> bool:
    if pattern.is_regex:
        return re.search(pattern.value, haystack, re.IGNORECASE) is not None
    return pattern.value.lower() in haystack.lower()


def _extract_evidence(redacted_message: str, rule: FingerprintRule) -> str:
    for line in redacted_message.splitlines():
        if _line_matches_rule(line=line, rule=rule):
            return line.strip()[:500]

    return redacted_message.replace("\n", " ")[:500].strip()


def _line_matches_rule(line: str, rule: FingerprintRule) -> bool:
    return any(_matches_pattern(pattern, line) for pattern in rule.patterns) or any(
        term.lower() in line.lower()
        for term in rule.required_terms
    )
