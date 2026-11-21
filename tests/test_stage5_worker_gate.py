"""N07 must require Qwen yes on the actual N05 visual claim (not CLIP score)."""
import hashlib
import unittest
from qa.legacy_offline_worker import gate_source_n07
SHA=hashlib.sha256(b"test video").hexdigest()
H="a"*64
def inputs():
    claim={"claim_id":"C1","text":"A red square and blue circle.",
          "source_sha256":SHA,"verdict":"VISUAL_DIRECT","evidence_ids":["V1"]}
    visual={"id":"V1","start_s":0.,"end_s":2.,"source_sha256":SHA,
            "description":"A red square and blue circle.","frame_sha256":H}
    return claim,visual
class N07Stage5WorkerTests(unittest.TestCase):
    def test_qwen_yes_lets_source_pass_even_when_clip_distractor_has_higher_score(self):
        claim,vis=inputs()
        result=gate_source_n07(SHA,2.5,claim,vis,H,[0.21,0.32,0.05],"YES")
        self.assertEqual(result["status"],"TENTATIVE_VISUAL_CANDIDATE")
        self.assertEqual(result["clip_source_rank_total_candidates"],2)
        self.assertEqual(result["original_claim_id"],"C1")
        self.assertFalse(result["approved_for_render"])
    def test_qwen_no_cannot_approve_source_even_if_clip_score_high(self):
        claim,vis=inputs()
        result=gate_source_n07(SHA,2.5,claim,vis,H,[0.5,0.1,0.05],"NO")
        self.assertEqual(result["status"],"UNRESOLVED")
    def test_wrong_frame_bytes_fail_even_when_qwen_says_yes(self):
        claim,vis=inputs()
        with self.assertRaisesRegex(ValueError,"frame"):
            gate_source_n07(SHA,2.5,claim,vis,"b"*64,[0.5],"YES")
    def test_replaced_claim_text_cannot_steal_qwen_yes(self):
        claim,vis=inputs();claim["text"]="The man fires a gun."
        with self.assertRaisesRegex(ValueError,"claim"):
            gate_source_n07(SHA,2.5,claim,vis,H,[0.5],"YES")
if __name__=="__main__":unittest.main()
