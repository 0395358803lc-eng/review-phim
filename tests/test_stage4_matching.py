"""No cross-stage claim can silently rebind to a different source shot."""
import hashlib
import sys
from pathlib import Path
import unittest
from stage4.matching import bind_sentences_to_shots

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"skills"/"film-review-orchestrator"/"scripts"))
import evidence_qc
SHA=hashlib.sha256(b"synthetic original").hexdigest()

def sample():
    return dict(source_sha256=SHA,source_duration_s=5,voice_duration_s=4,
      catalog={
        "V1":{"kind":"visual","text":"A red square.","start_s":0.,"end_s":2.,"source_sha256":SHA},
        "A1":{"kind":"asr","text":"Đây là hình vuông.","start_s":2.,"end_s":4.,"source_sha256":SHA}},
      sentences=[
       {"sentence_id":"S0001","review_text":"Hình ảnh ghi nhận: A red square.",
        "atomic_claims":[{"claim_id":"C0001","text":"A red square.",
          "verdict":"VISUAL_DIRECT","evidence_ids":["V1"],"source_sha256":SHA}]},
       {"sentence_id":"S0002","review_text":"Lời thoại ghi nhận: “Đây là hình vuông.”",
        "atomic_claims":[{"claim_id":"C0002","text":"Đây là hình vuông.",
          "verdict":"DIALOGUE_SUPPORTED","evidence_ids":["A1"],"source_sha256":SHA}]}],
      voice_timeline=[
         {"sentence_id":"S0001","voice_start_s":0.,"voice_end_s":2.},
         {"sentence_id":"S0002","voice_start_s":2.,"voice_end_s":4.}],
      chosen={"S0001":"V1","S0002":"A1"})

class Stage4CrossStageTests(unittest.TestCase):
    def test_two_sentences_reuse_actual_claim_ids_and_provenance(self):
        doc=bind_sentences_to_shots(**sample())
        self.assertEqual(len(doc["sentences"]),2)
        self.assertEqual(doc["sentences"][0]["atomic_claims"][0]["claim_id"],"C0001")
        self.assertEqual(doc["sentences"][1]["chosen_shots"][0]["asr_evidence_ids"],["A1"])
        self.assertEqual(doc["sentences"][1]["chosen_shots"][0]["verdict"],"DIALOGUE_SUPPORTED")
        self.assertEqual(evidence_qc.validate_map(doc),[])
    def test_changed_visual_id_cannot_be_substituted(self):
        x=sample();x["chosen"]["S0001"]="A1"
        with self.assertRaisesRegex(ValueError,"claim|evidence"):
            bind_sentences_to_shots(**x)
    def test_mismatched_source_evidence_hash_fails(self):
        x=sample();x["catalog"]["V1"]["source_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"source"):
            bind_sentences_to_shots(**x)
    def test_voice_timing_must_match_actual_sentence(self):
        x=sample();x["voice_timeline"][0]["sentence_id"]="INVALID"
        with self.assertRaises(ValueError):
            bind_sentences_to_shots(**x)
    def test_unsupported_claim_is_not_allowed_into_render_map(self):
        x=sample();x["sentences"][0]["atomic_claims"][0]["verdict"]="UNRESOLVED"
        with self.assertRaises(ValueError):
            bind_sentences_to_shots(**x)
if __name__=="__main__":
    unittest.main()
