from __future__ import annotations

import json
import base64
import tempfile
import unittest
import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch

from synthetic_harness.authoring import (
    find_forbidden_keys,
    require_keys,
)
from synthetic_harness.adjudication import record_adjudication
from synthetic_harness.arms import result_contract, result_schema
from synthetic_harness.episode import Episode
from synthetic_harness.patient_actor import (
    RESPONSE_FOOTER,
    RESPONSE_HEADER,
    parse_patient_response,
)
from synthetic_harness.results import validate_arm_result
from synthetic_harness.results import ingest_arm_result
from synthetic_harness.metrics import build_metrics
from synthetic_harness.evaluation import validate_verdict
from synthetic_harness.source_review import record_source_review
from synthetic_harness.source_review import latest_source_reviews, source_fingerprint
from synthetic_harness.sandboxing import write_web_read_barrier
from synthetic_harness.server import (
    create_direct_episode,
    live_agent_events,
    patient_submission_snapshot,
    summarize_live_command,
)


class EpisodeTests(unittest.TestCase):
    def valid_result(self, episode: Episode, arm: str, title: str) -> dict:
        source = {
            "title": title,
            "source_type": "official policy",
            "evidence_role": "governing_policy",
            "url": "https://example.invalid/policy",
            "path": None,
            "local_snapshot_path": None,
            "effective_date": "2026-01-01",
            "sha256": None,
            "official": True,
            "current": True,
            "applicable": True,
        }
        return {
            "episode_id": episode.episode_id,
            "arm": arm,
            "status": "actionable_result",
            "case_identification": {},
            "retrieval": {
                "candidates": [],
                "selected_source": source,
                "citations": [],
            },
            "policy_analysis": {},
            "patient_interaction": {
                "questions": [],
                "provider_records_needed": [],
                "question_stop_reason": "No further question.",
            },
            "next_steps": {"primary_action": "Contact the provider."},
            "confidence": {"overall": "medium"},
            "blockers": [],
        }

    def test_episode_and_messages_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary), label="test")
            first = episode.create_message(
                sender="orchestrator",
                recipient="patient_actor",
                body="BEGIN PATIENT EPISODE",
                message_type="episode_start",
            )
            second = episode.create_message(
                sender="patient_actor",
                recipient="orchestrator",
                body="I received the denial letter.",
                in_reply_to=first["message_id"],
            )
            self.assertEqual(first["sequence"], 1)
            self.assertEqual(second["sequence"], 2)
            self.assertTrue(episode.verify()["valid"])

    def test_live_web_activity_is_sanitized_for_ui(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            events_path = (
                episode.root / "system" / "web_only" / "codex_events.jsonl"
            )
            events_path.write_text(
                json.dumps(
                    {
                        "type": "item.started",
                        "item": {
                            "type": "command_execution",
                            "command": (
                                "curl 'https://html.duckduckgo.com/html/"
                                "?q=Aetna+knee+arthroplasty'"
                            ),
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            activity = live_agent_events(
                episode,
                "web_only",
                {"status": "running"},
            )
            self.assertEqual(len(activity), 1)
            self.assertIn("Searching the web", activity[0]["summary"])
            self.assertTrue(activity[0]["volatile"])
            self.assertIn(
                "Verifying",
                summarize_live_command("shasum -a 256 policy.pdf"),
            )

    def test_tampered_message_fails_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            envelope = episode.create_message(
                sender="orchestrator",
                recipient="patient_actor",
                body="Original",
            )
            path = next((episode.root / "patient_workspace" / "inbox").glob("*.json"))
            data = json.loads(path.read_text(encoding="utf-8"))
            data["body"] = "Changed"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = episode.verify()
            self.assertFalse(result["valid"])
            self.assertTrue(result["message_errors"])

    def test_tampered_log_fails_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            path = episode.root / "system" / "logs" / "shared.events.jsonl"
            rows = path.read_text(encoding="utf-8").splitlines()
            record = json.loads(rows[0])
            record["summary"] = "Tampered"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            self.assertFalse(episode.verify()["valid"])

    def test_patient_packet_rejects_answer_key_fields(self) -> None:
        findings = find_forbidden_keys(
            {
                "persona": {},
                "nested": {
                    "source_id": "must-not-leak",
                    "safe": "value",
                },
            }
        )
        self.assertEqual(findings, ["$.nested.source_id"])

    def test_required_schema_fields_are_checked(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            require_keys({"persona": {}}, {"persona", "insurance_card"}, "packet")

    def test_patient_response_parser(self) -> None:
        text = f"""{RESPONSE_HEADER}
episode_id: ep_123
case_id: case_456
in_reply_to: msg_789
body:
I am not sure when physical therapy started.
{RESPONSE_FOOTER}"""
        parsed = parse_patient_response(text)
        self.assertEqual(parsed["episode_id"], "ep_123")
        self.assertEqual(parsed["in_reply_to"], "msg_789")
        self.assertEqual(parsed["body"], "I am not sure when physical therapy started.")

    def test_patient_response_parser_rejects_extra_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "required patient-actor envelope"):
            parse_patient_response("Here is my analysis.")

    def test_result_contract_requires_core_outputs(self) -> None:
        contract = result_contract()
        self.assertIn("retrieval", contract["required_top_level_fields"])
        self.assertIn("patient_interaction", contract["required_top_level_fields"])
        self.assertIn("actionable_result", contract["status_values"])
        schema = result_schema()
        self.assertIn("retrieval", schema["required"])
        self.assertEqual(schema["properties"]["arm"]["enum"], ["library_only", "web_only"])

    def test_supporting_document_cannot_be_actionable_policy_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            result = self.valid_result(episode, "library_only", "Supporting form")
            result["retrieval"]["selected_source"]["evidence_role"] = "supporting_document"
            errors = validate_arm_result(result, episode, "library_only")
            self.assertIn(
                "actionable result requires selected_source.evidence_role=governing_policy",
                errors,
            )

    def test_invalid_arm_result_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            errors = validate_arm_result(
                {
                    "episode_id": episode.episode_id,
                    "arm": "library_only",
                    "status": "actionable_result",
                },
                episode,
                "library_only",
            )
            self.assertIn("missing top-level field: retrieval", errors)
            self.assertIn("actionable result requires a selected source", errors)

    def test_source_confirmation_is_hash_chained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            result_path = episode.root / "system" / "library_only" / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "retrieval": {
                            "selected_source": {
                                "title": "Synthetic policy",
                                "path": "not-rendered.pdf",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            feedback = record_source_review(
                episode=episode,
                arm="library_only",
                decision="confirmed",
                notes="Correct payer and procedure.",
            )
            self.assertEqual(feedback["decision"], "confirmed")
            self.assertTrue(episode.verify()["valid"])
            with self.assertRaisesRegex(ValueError, "already has"):
                record_source_review(
                    episode=episode,
                    arm="library_only",
                    decision="rejected",
                )

    def test_replacement_source_is_saved_and_committed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            result_path = episode.root / "system" / "web_only" / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "retrieval": {
                            "selected_source": {
                                "title": "Wrong synthetic policy",
                                "url": "https://example.invalid/policy",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            feedback = record_source_review(
                episode=episode,
                arm="web_only",
                decision="replaced",
                upload={
                    "name": "replacement.txt",
                    "media_type": "text/plain",
                    "base64": base64.b64encode(b"replacement policy").decode(),
                },
            )
            replacement = feedback["replacement_source"]
            self.assertTrue((episode.root / replacement["path"]).exists())
            self.assertEqual(replacement["bytes"], len(b"replacement policy"))
            self.assertTrue(episode.verify()["valid"])

    def test_fake_pdf_replacement_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            result_path = episode.root / "system" / "web_only" / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "retrieval": {
                            "selected_source": {
                                "title": "Wrong policy",
                                "url": "https://example.invalid",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "PDF signature"):
                record_source_review(
                    episode=episode,
                    arm="web_only",
                    decision="replaced",
                    upload={
                        "name": "fake.pdf",
                        "media_type": "application/pdf",
                        "base64": base64.b64encode(b"not a pdf").decode(),
                    },
                )

    def test_source_review_carries_across_same_source_follow_up(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            source = {
                "title": "Same policy",
                "url": "https://example.invalid/same",
                "sha256": "abc",
            }
            result_path = episode.root / "system" / "library_only" / "result.json"
            result_path.write_text(
                json.dumps({"retrieval": {"selected_source": source}}),
                encoding="utf-8",
            )
            record_source_review(
                episode=episode,
                arm="library_only",
                decision="confirmed",
            )
            reviews = latest_source_reviews(
                episode,
                active_source_fingerprints={
                    "library_only": source_fingerprint(source)
                },
            )
            self.assertEqual(reviews["library_only"]["decision"], "confirmed")

    def test_correction_result_versions_without_overwriting_original(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            arm_root = episode.root / "system" / "library_only"
            (arm_root / "result.json").write_text(
                json.dumps(self.valid_result(episode, "library_only", "Original")),
                encoding="utf-8",
            )
            ingest_arm_result(episode, "library_only")
            original = json.loads((arm_root / "frozen_result.json").read_text())
            revision = arm_root / "revisions" / "rev_001"
            revision.mkdir(parents=True)
            (revision / "result.json").write_text(
                json.dumps(self.valid_result(episode, "library_only", "Corrected")),
                encoding="utf-8",
            )
            ingest_arm_result(episode, "library_only", revision)
            active = json.loads((arm_root / "active_result.json").read_text())
            preserved = json.loads((arm_root / "frozen_result.json").read_text())
            self.assertEqual(original["retrieval"]["selected_source"]["title"], "Original")
            self.assertEqual(preserved["retrieval"]["selected_source"]["title"], "Original")
            self.assertEqual(active["retrieval"]["selected_source"]["title"], "Corrected")
            self.assertTrue(episode.verify()["valid"])

    def test_human_adjudication_is_appended_to_integrity_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            verdict_path = episode.root / "evaluation" / "automated_verdict.json"
            verdict_path.write_text(
                json.dumps({"human_review_priority": "routine"}),
                encoding="utf-8",
            )
            record = record_adjudication(
                episode=episode,
                decision="confirmed",
                notes="Reviewed against the sealed fixture.",
            )
            self.assertEqual(record["decision"], "confirmed")
            self.assertTrue(episode.verify()["valid"])

    def test_metrics_exclude_skips_from_accuracy_denominator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            episode = Episode.create(root)
            log = episode.root / "review" / "source_feedback.jsonl"
            from synthetic_harness.integrity import HashChainLog

            HashChainLog(log).append(
                {"arm": "library_only", "decision": "confirmed"}
            )
            HashChainLog(log).append(
                {"arm": "library_only", "decision": "skipped"}
            )
            metrics = build_metrics(root)
            library = metrics["arms"]["library_only"]
            self.assertEqual(library["judged_source_selections"], 1)
            self.assertEqual(library["confirmed_accuracy"], 1.0)

    def test_web_barrier_denies_internal_policy_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "episode/system/web_only"
            library = root / "library"
            platform = root / "platform"
            run_dir.mkdir(parents=True)
            library.mkdir()
            platform.mkdir()
            profile = write_web_read_barrier(
                workspace=root,
                episode_root=root / "episode",
                run_dir=run_dir,
                source_library_root=library,
                platform_root=platform,
            )
            text = profile.read_text()
            self.assertIn(str(library.resolve()), text)
            self.assertIn(str(platform.resolve()), text)
            self.assertIn("(deny file-read*", text)
            sandbox_exec = shutil.which("sandbox-exec")
            if sandbox_exec:
                secret = library / "secret.txt"
                allowed = run_dir / "allowed.txt"
                secret.write_text("secret")
                allowed.write_text("allowed")
                allowed_run = subprocess.run(
                    [sandbox_exec, "-f", str(profile), "/bin/cat", str(allowed)],
                    capture_output=True,
                    text=True,
                )
                denied_run = subprocess.run(
                    [sandbox_exec, "-f", str(profile), "/bin/cat", str(secret)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(allowed_run.returncode, 0)
                self.assertNotEqual(denied_run.returncode, 0)

    def test_invalid_evaluator_scores_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Episode.create(Path(temporary))
            episode._update_manifest(requested_arms=["library_only"])
            errors = validate_verdict(
                episode,
                {
                    "episode_id": episode.episode_id,
                    "arms": {
                        "library_only": {
                            "retrieval": {"score": 9, "max_score": 4},
                        }
                    },
                    "human_review_priority": "routine",
                    "summary": "Invalid test",
                },
            )
            self.assertIn(
                "library_only.retrieval.score must be 0-4",
                errors,
            )

    def test_direct_episode_restores_patient_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            from unittest.mock import patch

            with patch(
                "synthetic_harness.server.EPISODES_ROOT",
                Path(temporary),
            ):
                episode = create_direct_episode(
                    {
                        "denial_letter": "Synthetic denial",
                        "payer": "Example",
                        "retrieval_mode": "library_only",
                    }
                )
            restored = patient_submission_snapshot(episode)
            self.assertEqual(restored["denial_letter"], "Synthetic denial")
            self.assertEqual(restored["payer"], "Example")


if __name__ == "__main__":
    unittest.main()
