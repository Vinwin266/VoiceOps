import json
import tempfile
import unittest

from app.voiceops.analyzer import analyze_jsonl
from app.voiceops.events.normalizer import normalize_logs
from app.voiceops.fingerprints.matcher import match_fingerprints
from app.voiceops.graph.graph import run_rca_graph
from app.voiceops.rca.report_builder import build_rca_report
from app.voiceops.sinks.jsonl import append_events
from app.voiceops.sources.jsonl import load_jsonl_events, parse_jsonl_events


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
            (
                "SIP INVITE failed with status_code=503 trunk=primary",
                "SIP_INVITE_FAILED",
                "sip_invite",
            ),
            (
                "provider webhook failed status_code=500 call_sid=CA123",
                "PROVIDER_WEBHOOK_FAILED",
                "provider_webhook",
            ),
            (
                "participant failed to join room after timeout",
                "PARTICIPANT_JOIN_TIMEOUT",
                "participant_join",
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
                self.assertEqual(report.event_count, len(events))
                self.assertEqual(report.matched_event_ids, [events[0].event_id])

    def test_unknown_logs_return_unknown_failure_report(self) -> None:
        events = normalize_logs("unexpected failure with no known terms", run_id=456)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)

        self.assertEqual(report.primary_fingerprint, "UNKNOWN_VOICEOPS_FAILURE")
        self.assertEqual(report.phase, "unknown")
        self.assertEqual(report.module, "unknown")
        self.assertEqual(report.confidence, 0.2)
        self.assertIsNone(report.taxonomy_confidence)
        self.assertEqual(report.evidence, ["unexpected failure with no known terms"])
        self.assertIsNone(report.primary_event_id)
        self.assertEqual(report.matched_event_ids, [])

    def test_optional_taxonomy_terms_do_not_classify_by_themselves(self) -> None:
        events = normalize_logs("model response looked unusual", run_id=456)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)

        self.assertEqual(report.primary_fingerprint, "UNKNOWN_VOICEOPS_FAILURE")
        self.assertEqual(report.phase, "unknown")
        self.assertEqual(report.module, "unknown")
        self.assertIsNone(report.taxonomy_confidence)

    def test_unknown_classifiable_logs_use_inferred_phase(self) -> None:
        events = normalize_logs("participant waiting to join room", run_id=457)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)

        self.assertEqual(report.primary_fingerprint, "UNKNOWN_VOICEOPS_FAILURE")
        self.assertEqual(report.phase, "participant_join")
        self.assertEqual(report.module, "session_orchestrator")
        self.assertEqual(report.confidence, 0.4)
        self.assertEqual(report.taxonomy_confidence, 0.4)
        self.assertEqual(report.primary_event_id, events[0].event_id)
        self.assertEqual(
            report.primary_root_cause,
            "Unknown failure during LiveKit participant join.",
        )
        self.assertIn("room_id", report.recommended_fix)
        self.assertIn("dispatch_id and room lifecycle logs.", report.next_evidence_needed)

    def test_unknown_llm_logs_use_phase_specific_next_evidence(self) -> None:
        events = normalize_logs("llm_node timed out waiting for provider response", run_id=458)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)

        self.assertEqual(report.primary_fingerprint, "UNKNOWN_VOICEOPS_FAILURE")
        self.assertEqual(report.phase, "llm")
        self.assertEqual(report.module, "llm")
        self.assertEqual(report.primary_root_cause, "Unknown failure during LLM provider execution.")
        self.assertIn("model_or_deployment.", report.next_evidence_needed)

    def test_source_module_maps_to_canonical_module(self) -> None:
        raw_jsonl = json.dumps(
            {
                "raw_message": "participant waiting to join room",
                "source_module": "my_app.v1_entrypoint",
            }
        )

        events = parse_jsonl_events(raw_jsonl, run_id=459)

        self.assertEqual(events[0].source_module, "my_app.v1_entrypoint")
        self.assertEqual(events[0].canonical_module, "session_orchestrator")
        self.assertEqual(events[0].module, "session_orchestrator")

    def test_jsonl_sink_and_source_round_trip_events(self) -> None:
        events = normalize_logs("SIP INVITE failed with status_code=503", run_id=460)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/events.jsonl"
            append_events(events, path=path)
            loaded_events = load_jsonl_events(path)

        report = build_rca_report(
            events=loaded_events,
            matches=match_fingerprints(loaded_events),
        )

        self.assertEqual(len(loaded_events), 1)
        self.assertEqual(loaded_events[0].event_id, events[0].event_id)
        self.assertEqual(report.primary_fingerprint, "SIP_INVITE_FAILED")

    def test_jsonl_analyzer_uses_same_rca_pipeline(self) -> None:
        raw_jsonl = json.dumps(
            {
                "raw_message": "provider webhook failed status_code=500 call_sid=CA123",
                "source_module": "twilio.webhook_handler",
                "provider": "twilio",
                "call_sid": "CA123",
            }
        )

        report = analyze_jsonl(raw_jsonl, run_id=461)

        self.assertEqual(report.primary_fingerprint, "PROVIDER_WEBHOOK_FAILED")
        self.assertEqual(report.phase, "provider_webhook")
        self.assertEqual(report.module, "telephony_provider")

    def test_langgraph_wrapper_runs_deterministic_pipeline(self) -> None:
        result = run_rca_graph(
            {
                "raw_input": "SIP INVITE failed with status_code=503 trunk=primary",
                "run_id": 462,
            }
        )
        report = result.get("report")

        if report is None:
            self.fail("RCA graph did not return a report")
        self.assertEqual(report.primary_fingerprint, "SIP_INVITE_FAILED")

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

    def test_known_fingerprint_uses_redacted_log_snippet_as_evidence(self) -> None:
        raw_log = (
            "Error code: 404 - DeploymentNotFound from chat.completions.create "
            "token=supersecret user=person@example.com"
        )

        events = normalize_logs(raw_log, run_id=790)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)

        self.assertEqual(report.primary_fingerprint, "LLM_DEPLOYMENT_NOT_FOUND")
        self.assertEqual(
            report.evidence,
            [
                "Error code: 404 - DeploymentNotFound from chat.completions.create "
                "token=[redacted] user=[email]"
            ],
        )
        self.assertEqual(report.matched_event_ids, [events[0].event_id])

    def test_report_serializes_to_expected_result_contract(self) -> None:
        events = normalize_logs("DeploymentNotFound", run_id=789)
        matches = match_fingerprints(events)
        report = build_rca_report(events=events, matches=matches)
        payload = json.loads(report.model_dump_json())

        self.assertEqual(payload["status"], "rca_completed")
        self.assertEqual(payload["primary_fingerprint"], "LLM_DEPLOYMENT_NOT_FOUND")
        self.assertEqual(payload["phase"], "llm")
        self.assertEqual(payload["module"], "v1_agent / llm_node")
        self.assertEqual(payload["severity"], "high")
        self.assertTrue(payload["summary"])
        self.assertEqual(payload["confidence"], 0.95)
        self.assertEqual(
            payload["primary_root_cause"],
            "Configured LLM deployment was not found.",
        )
        self.assertEqual(payload["evidence"], ["DeploymentNotFound"])
        self.assertEqual(payload["suspected_owner"], "llm_provider_config")
        self.assertTrue(payload["next_evidence_needed"])
        self.assertEqual(payload["event_count"], 1)
        self.assertEqual(payload["primary_event_id"], events[0].event_id)
        self.assertEqual(payload["taxonomy_confidence"], 0.6)
        self.assertEqual(payload["matched_event_ids"], [events[0].event_id])
        self.assertEqual(payload["matched_fingerprints"], [])


if __name__ == "__main__":
    unittest.main()
