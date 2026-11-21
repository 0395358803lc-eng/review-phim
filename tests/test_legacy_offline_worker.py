"""QA-only local provider contract regression; real GPU acceptance is separate."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from qa.legacy_offline_worker import read_contract,record_provider_verification

class LocalWorkerContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.job=self.root/"job";self.job.mkdir()
        self.out=self.job/".engine21"/"attempts"/"N02"/"0001"
        self.out.mkdir(parents=True)
        self.src=self.root/"source.mp4";self.src.write_bytes(b"synthetic-media")
        self.sha=hashlib.sha256(self.src.read_bytes()).hexdigest()
        self.env={"FRA_JOB":str(self.job),"FRA_STAGE":"N02",
          "FRA_SOURCE":str(self.src),"FRA_OUTPUT_DIR":str(self.out),
          "FRA_SOURCE_SHA256":self.sha,
          "FRA_REQUIRED_OUTPUTS":'["transcript_original.jsonl","transcript_vi.jsonl","uncertainties.jsonl"]',
          "FRA_REQUIRED_CHECKS":'["asr_timestamp_in_range","unclear_speech_disclosed"]'}
    def test_engine_forwards_only_approved_offline_model_cache_environment(self):
        from unittest.mock import patch
        from engine21.runner import provider_environment
        with patch.dict("os.environ",{
            "HF_HOME":"C:/qa/cache","HF_HUB_OFFLINE":"1",
            "TRANSFORMERS_OFFLINE":"1","TORCH_HOME":"C:/qa/torch",
            "MALICIOUS_UNRELATED_SECRET":"do-not-leak"}):
            env=provider_environment()
        self.assertEqual(env["HF_HOME"],"C:/qa/cache")
        self.assertEqual(env["HF_HUB_OFFLINE"],"1")
        self.assertEqual(env["TRANSFORMERS_OFFLINE"],"1")
        self.assertEqual(env["TORCH_HOME"],"C:/qa/torch")
        self.assertNotIn("MALICIOUS_UNRELATED_SECRET",env)
    def test_context_rejects_wrong_source_hash(self):
        self.env["FRA_SOURCE_SHA256"]="0"*64
        with self.assertRaises(ValueError):
            read_contract(self.env)
    def test_provider_verification_is_bound_to_actual_stage_and_source(self):
        ctx=read_contract(self.env)
        result=record_provider_verification(ctx,"real-whisper-test",
             input_media_synthetic=True)
        self.assertEqual(result["source_sha256"],self.sha)
        self.assertFalse(result["synthetic_fixture"])
        self.assertTrue(result["input_media_synthetic"])
        saved=json.loads((self.out/"provider_verification.json").read_text())
        self.assertEqual(set(saved["checks"]),{"asr_timestamp_in_range","unclear_speech_disclosed"})

if __name__=="__main__":
    unittest.main()
