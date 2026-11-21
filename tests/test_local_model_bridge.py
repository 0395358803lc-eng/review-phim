"""Cross-modal acceptance tests on tiny manifests, no real model dependencies."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa.local_model_bridge import verify_model_reports

def hash_bytes(blob:bytes)->str:
    return hashlib.sha256(blob).hexdigest()

class LegacyModelBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.voice=Path(self.tmp.name)/"synthetic.wav"
        self.voice.write_bytes(b"RIFF_TEST_TONE_12345")
        self.qwen_path=Path(self.tmp.name)/"qwen.json"
        self.qwen={"status":"PASS","model":"Qwen/Qwen3-VL-2B-Instruct",
                   "generated_text":"A red square and a blue circle."}
        self.qwen_path.write_text(json.dumps(self.qwen))
        self.clip={"status":"PASS",
           "qwen_report_sha256":hash_bytes(self.qwen_path.read_bytes()),
           "query_texts":["A red square and a blue circle.","a green square"],
           "candidates":["QWEN_SOURCE_FRAME","DISTRACTOR_GREEN"],
           "ranks":[["QWEN_SOURCE_FRAME","DISTRACTOR_GREEN"]],
           "clip_embedding_dim":512,"correct_source_rank":1}
        self.tts={"status":"PASS","wav_sha256":hash_bytes(self.voice.read_bytes()),
                  "source_text":"Trong cảnh thử nghiệm có một hình vuông đỏ và một hình tròn xanh.",
                  "sample_rate":48000}
        self.asr={"status":"PASS","device":"cuda",
                  "wav_sha256":hash_bytes(self.voice.read_bytes()),
                  "segments":[{"start_s":0,"end_s":3,
                  "text":"Trong cảnh thử nghiệm có một hình vuông đỏ và một hình tròn xanh."}]}
    def check(self):
        return verify_model_reports(self.qwen_path,self.clip,self.tts,self.asr,self.voice)
    def test_four_model_reports_bind_real_caption_and_voice(self):
        evidence=self.check()
        self.assertEqual(evidence["source_frame_rank"],1)
        self.assertGreaterEqual(evidence["speech_similarity"],0.95)
    def test_wrong_clip_qwen_digest_rejected(self):
        self.clip["qwen_report_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Qwen"):
            self.check()
    def test_wrong_voice_hash_rejected(self):
        self.asr["wav_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"voice|WAV"):
            self.check()
    def test_unrelated_recognition_cannot_pass(self):
        self.asr["segments"][0]["text"]="Không nghe rõ bất kỳ từ nào."
        with self.assertRaisesRegex(ValueError,"speech"):
            self.check()

if __name__=="__main__":
    unittest.main()
