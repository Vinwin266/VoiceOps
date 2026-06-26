import json
import unittest

from app.voiceops.events.normalizer import normalize_logs
from app.voiceops.fingerprints.matcher import match_fingerprints
from app.voiceops.rca.report_builder import build_rca_report


class VoiceOpsRCATest(unittest.TestCase):
    def test_known_fingerprints_match_expected_phases(self) -> None:
        cases = [
            (
                "openai error: DeploymentNotFound for configured model",
                "LLM_DEPLOYMENT_NOT_FOUND",
                "llm",
            ),
            (
                "asyncio: Task exception was never retrieved",
                "UNOBSERVED_ASYNC_TASK_EXCEPTION",
                "async_runtime",
            ),
            (
                "LiveKit failure: Session is closed",
                "LIVEKIT_SESSION_CLOSED",
                "dispatch/session_lifecycle",
            ),
            (
                "TypeError: MockSession.say unexpected keyword allow_interruptions",
                "SESSION_SAY_SIGNATURE_MISMATCH",
                "tool/test_runtime",
            ),
        ]

        for raw_log, fingerprint, phase in cases:
            with self.subTest(fingerprint=fingerprint):
                events = normalize_logs(raw_log, run_id=123)
                matches = match_fingerprints(events)
                report = build_rca_report(events=events, matches=matches)

                self.assertEqual(report.primary_fingerprint, fingerprint)
                self.assertEqual(report.phase, phase)
                self.assertGreaterEqual(report.confidence, 0.9)
                self.assertTrue(report.evidence)
                self.assertTrue(report.recommended_fix)
                self.assertTrue(report.verification_plan)

    def test_unknown_logs_return_unknown_failure_report(self) -> None:
        events = normalize_logs("caller hung up after a long silence", run_id=456)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)

        self.assertEqual(report.primary_fingerprint, "UNKNOWN_VOICEOPS_FAILURE")
        self.assertEqual(report.phase, "unknown")
        self.assertEqual(report.module, "unknown")
        self.assertEqual(report.confidence, 0.2)
        self.assertEqual(report.evidence, ["caller hung up after a long silence"])

    def test_traceback_lines_are_grouped_into_one_event(self) -> None:
        raw_log = """
ERROR llm_node failed
Traceback (most recent call last):
  File "/app/voice.py", line 10, in run_turn
    call_llm()
  File "/app/llm.py", line 22, in call_llm
    raise DeploymentNotFound()
DeploymentNotFound: configured deployment does not exist
INFO monitor recovered
"""

        events = normalize_logs(raw_log, run_id=789)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)

        self.assertEqual(len(events), 2)
        self.assertIn("ERROR llm_node failed", events[0].raw_message)
        self.assertIn("Traceback (most recent call last):", events[0].raw_message)
        self.assertIn('  File "/app/voice.py"', events[0].raw_message)
        self.assertIn("DeploymentNotFound", events[0].raw_message)
        self.assertEqual(events[1].raw_message, "INFO monitor recovered")
        self.assertEqual(report.primary_fingerprint, "LLM_DEPLOYMENT_NOT_FOUND")

    def test_report_serializes_to_expected_result_contract(self) -> None:
        events = normalize_logs("DeploymentNotFound", run_id=789)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)
        payload = json.loads(report.model_dump_json())

        self.assertEqual(payload["status"], "rca_completed")
        self.assertEqual(payload["primary_fingerprint"], "LLM_DEPLOYMENT_NOT_FOUND")
        self.assertEqual(payload["phase"], "llm")
        self.assertEqual(payload["module"], "v1_agent / llm_node")
        self.assertEqual(payload["confidence"], 0.95)
        self.assertEqual(
            payload["primary_root_cause"],
            "Configured LLM deployment was not found.",
        )
        self.assertEqual(payload["evidence"], ["DeploymentNotFound"])
        self.assertEqual(payload["matched_fingerprints"], [])


if __name__ == "__main__":
    unittest.main()
