"""Approval pack creates UNSIGNED requests; Engine21 signer remains external."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"skills"/"film-review-orchestrator"/"scripts"))
import jobctl
from engine21 import state
from stage4.approval_requests import make_request,save_request

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class HumanApprovalRequestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        source=self.root/"synthetic_source.mp4";source.write_bytes(b"synthetic_source_only")
        self.job=jobctl.create_job(source,self.root/"jobs","synthetic request",probe=False)
        stage5=self.job/".engine21"/"attempts"/"N05"/"0001"
        stage5.mkdir(parents=True,exist_ok=True)
        self.script=stage5/"review_final.txt";self.script.write_text("Demo only.")
        self.evidence=stage5/"evidence.json";self.evidence.write_text('{"stage":"N05"}')
        self.job_id=jobctl.read_job(self.job)["job_id"]
        self.state={"engine_version":"2.1.0","job_id":self.job_id,
             "source_sha256":sha(source),
             "stages":{"N05":{"status":"DONE",
                 "evidence_path":str(self.evidence.relative_to(self.job)),
                 "evidence_sha256":sha(self.evidence),
                 "artifacts":[{"path":str(self.script.relative_to(self.job)),
                               "sha256":sha(self.script)}]}}}
        state.atomic_state(self.job,self.state)

    def test_script_request_uses_engine_evidence_subject_not_text_hash(self):
        request=make_request(self.job,"script")
        self.assertEqual(request["job_id"],self.job_id)
        self.assertEqual(request["subject_sha256"],sha(self.evidence))
        self.assertNotEqual(request["subject_sha256"],sha(self.script))
        self.assertEqual(request["review_text_sha256"],sha(self.script))
        self.assertEqual(request["gate"],"script")
        self.assertNotIn("signature",request)
        self.assertEqual(request["status"],"PENDING_HUMAN_DECISION")

    def test_voice_request_requires_existing_decodable_sample_and_sha(self):
        sample=self.job/"voice"/"approved_sample.wav"
        sample.parent.mkdir(exist_ok=True)
        with wave.open(str(sample),"wb") as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000)
            f.writeframes(b"\0\0"*1600)
        request=make_request(self.job,"voice")
        self.assertEqual(request["subject_sha256"],sha(sample))
        self.assertNotIn("signature",request)

    def test_voice_request_refuses_missing_media(self):
        with self.assertRaises((ValueError,FileNotFoundError)):
            make_request(self.job,"voice")

    def test_script_request_refuses_modified_evidence(self):
        self.evidence.write_text('{"tampered":true}')
        with self.assertRaisesRegex(ValueError,"evidence|SHA"):
            make_request(self.job,"script")

    def test_script_request_refuses_modified_review_text(self):
        self.script.write_text("Unapproved rewritten script")
        with self.assertRaisesRegex(ValueError,"review|SHA"):
            make_request(self.job,"script")

    def test_request_cannot_overwrite_and_is_not_a_signed_receipt(self):
        request=make_request(self.job,"script")
        saved=save_request(self.job,request)
        self.assertTrue(saved.is_file())
        with self.assertRaises(FileExistsError):
            save_request(self.job,request)
        self.assertNotIn("signature",json.loads(saved.read_text()))

if __name__=="__main__":
    unittest.main()
