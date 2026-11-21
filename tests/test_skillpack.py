"""Standalone pack contract tests. All fixtures are synthetic; no user media."""
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "skills" / "film-review-orchestrator"
sys.path.insert(0, str(CORE / "scripts"))
SKILLS = {
    "film-review-orchestrator", "film-intake", "scene-indexing", "speech-analysis",
    "visual-analysis", "story-memory", "review-writing", "voice-production",
    "semantic-matching", "video-editing", "quality-delivery",
}

class SkillPackagingTests(unittest.TestCase):
    def test_all_11_standard_skills_with_valid_discovery(self):
        import yaml
        actual = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
        self.assertEqual(actual, SKILLS)
        for name in SKILLS:
            body = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(body.startswith("---\n"), name)
            front = yaml.safe_load(body.split("---", 2)[1])
            self.assertEqual(front["name"], name)
            self.assertTrue(front["description"].startswith("Use when "), name)
            self.assertLessEqual(len(front["description"]), 1024)
            self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
            self.assertIn("## ", body)

    def test_no_old_pipeline_or_user_media_packaged(self):
        all_files = [p for p in ROOT.rglob("*") if p.is_file()]
        for p in all_files:
            self.assertNotIn(p.suffix.lower(), {".mp4", ".mov", ".mkv", ".wav", ".npz", ".sqlite"})
        for p in (ROOT / "skills").rglob("SKILL.md"):
            s = p.read_text(encoding="utf-8")
            self.assertNotIn("G01–G15", s)
            self.assertNotIn("D:\\Phim", s)
            self.assertNotIn("100% semantic match", s)

    def test_documented_scripts_and_templates_exist(self):
        for name in ("jobctl.py", "evidence_qc.py"):
            self.assertTrue((CORE / "scripts" / name).is_file())
        for name in ("job-state.schema.json", "stage-evidence.schema.json", "sentence-shot-map.schema.json"):
            p = CORE / "schemas" / name
            self.assertTrue(p.is_file())
            self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["type"], "object")
        self.assertTrue((CORE / "templates" / "adapter-config.example.json").is_file())

class JobStateTests(unittest.TestCase):
    def test_independent_job_and_bounded_stage_transition(self):
        import jobctl
        with tempfile.TemporaryDirectory() as temp:
            top = Path(temp)
            source = top / "movie-source.fake"
            source.write_bytes(b"SYNTHETIC-ORIGINAL-SOURCE\n")
            job = jobctl.create_job(source, top / "jobs", "Test-only movie", "vi", probe=False)
            data = jobctl.read_job(job)
            self.assertTrue(str(job).startswith(str(top / "jobs")))
            self.assertEqual(data["stages"]["N00"]["status"], "PENDING")
            self.assertEqual(data["stages"]["N01"]["status"], "PENDING")
            with self.assertRaises(ValueError):
                jobctl.complete_stage(job, "N01", "missing.json")
            self.assertEqual(jobctl.verify_source(job)["sha256_match"], True)
            source.write_bytes(b"CHANGED")
            self.assertFalse(jobctl.verify_source(job)["sha256_match"])

    def test_completion_needs_manifest_and_real_approval(self):
        import jobctl
        with tempfile.TemporaryDirectory() as temp:
            top = Path(temp)
            source = top / "movie-source.fake"
            source.write_bytes(b"TESTSOURCE")
            job = jobctl.create_job(source, top / "jobs", "Test-only", "vi", probe=False)
            (job / "ingest").mkdir(exist_ok=True)
            artifact = job / "ingest" / "source_manifest.json"
            artifact.write_text('{"fixture":true}', encoding="utf-8")
            evidence = {
                "stage": "N00", "outcome": "PASS", "source_sha256": jobctl.read_job(job)["source"]["sha256"],
                "checks": {"source_file_verified": True, "media_probe_verified": True, "decode_verified": True},
                "artifacts": [{"path": "ingest/source_manifest.json", "sha256": jobctl.sha256(artifact)}],
                "limitations": [], "reviewed_at_utc": "2026-11-21T00:00:00Z",
            }
            evidence_path = job / "n00_evidence.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            jobctl.complete_stage(job, "N00", "n00_evidence.json")
            self.assertEqual(jobctl.read_job(job)["stages"]["N00"]["status"], "DONE")
            with self.assertRaises(ValueError):
                jobctl.complete_stage(job, "N05", "n00_evidence.json")
            with self.assertRaises(ValueError):
                jobctl.record_approval(job, "script", "", "user")

class EvidenceTests(unittest.TestCase):
    def test_valid_source_time_and_dialogue_references(self):
        import evidence_qc
        example = {
            "source_movie_sha256": "a" * 64,
            "source_duration_s": 100,
            "narration_duration_s": 12.5,
            "sentences": [{
                "sentence_id": "S0001", "review_text": "Một người nói về tài liệu.",
                "voice_start_s": 0.0, "voice_end_s": 4.5,
                "atomic_claims": [{"claim_id": "C1", "text": "Có tài liệu", "verdict": "DIALOGUE_SUPPORTED", "evidence_ids": ["ASR001"]}],
                "chosen_shots": [{"source_start_s": 21.0, "source_end_s": 25.5,
                   "voice_start_s": 0.0, "voice_end_s": 4.5,
                   "visual_evidence_ids": [], "asr_evidence_ids": ["ASR001"],
                   "verdict": "DIALOGUE_SUPPORTED", "qualifier": "Không suy ra danh tính người nói."}],
                "unresolved_claims": [],
            }],
        }
        self.assertEqual(evidence_qc.validate_map(example), [])
        example["sentences"][0]["chosen_shots"][0]["asr_evidence_ids"] = []
        self.assertTrue(any("ASR" in err for err in evidence_qc.validate_map(example)))
        example["sentences"][0]["chosen_shots"][0]["asr_evidence_ids"] = ["ASR001"]
        example["sentences"][0]["chosen_shots"][0]["source_end_s"] = 102
        self.assertTrue(any("source_duration" in err for err in evidence_qc.validate_map(example)))

if __name__ == "__main__":
    unittest.main()

class SecurityAndTraceTests(unittest.TestCase):
    def test_evidence_path_cannot_escape_job(self):
        import jobctl
        with tempfile.TemporaryDirectory() as temp:
            top = Path(temp)
            (top / "job").mkdir()
            with self.assertRaises(ValueError):
                jobctl.inside_job(top / "job", "../file-outside.json")
            with self.assertRaises(ValueError):
                jobctl.inside_job(top / "job", "/absolute.json")

    def test_claim_evidence_must_exist_in_selected_shots(self):
        import evidence_qc
        template = json.loads((CORE / "templates" / "match-example.synthetic.json").read_text(encoding="utf-8"))
        template["sentences"][0]["atomic_claims"][0]["evidence_ids"] = ["ASR_WRONG"]
        self.assertTrue(any("claim evidence" in e for e in evidence_qc.validate_map(template)))

    def test_source_sha256_must_not_be_fabricated_by_matching_ledger(self):
        import evidence_qc
        template = json.loads((CORE / "templates" / "match-example.synthetic.json").read_text(encoding="utf-8"))
        template["source_movie_sha256"] = "not-a-real-sha"
        self.assertTrue(any("source_movie_sha256" in e for e in evidence_qc.validate_map(template)))
