"""CLIP similarity is not evidence; Qwen yes/no requires source exactness."""
import hashlib
import unittest
from stage5.visual_gate import select_visual_shot
SHA=hashlib.sha256(b"original movie").hexdigest()
F1="a"*64
F2="b"*64
def claim(ids=None,motion=False,verdict="VISUAL_DIRECT"):
    return {"claim_id":"C9","source_sha256":SHA,"text":"A postal worker stands by a van.",
            "verdict":verdict,"evidence_ids":ids or ["V2"],"requires_motion":motion}
def candidates():
    return [{"frame_id":"V1","source_sha256":SHA,"frame_sha256":F1,
             "start_s":20.,"end_s":20.2,"raw_cosine":0.33},
            {"frame_id":"V2","source_sha256":SHA,"frame_sha256":F2,
             "start_s":25.,"end_s":25.2,"raw_cosine":0.29}]
def decision(frame="V2",answer="YES",source=SHA,sha=F2,claim_id="C9"):
    return {"claim_id":claim_id,"frame_id":frame,"source_sha256":source,
            "frame_sha256":sha,"verdict":answer,"provider":"Qwen3-VL-2B",
            "claim_text_sha256":hashlib.sha256("A postal worker stands by a van.".encode("utf8")).hexdigest()}
class GuardTests(unittest.TestCase):
    def test_qwen_corrects_clip_rank_one_when_yes_on_rank_two(self):
        doc=select_visual_shot(SHA,claim(),candidates(),
             [decision("V1","NO",sha=F1),decision()],100.)
        self.assertEqual(doc["status"],"TENTATIVE_VISUAL_CANDIDATE")
        self.assertEqual(doc["selected_frame_id"],"V2")
        self.assertEqual(doc["clip_rank"],2)
        self.assertFalse(doc["approved_for_render"])
        self.assertEqual(doc["original_claim_id"],"C9")
    def test_no_verifier_must_not_be_auto_allowed(self):
        doc=select_visual_shot(SHA,claim(),candidates(),[],100.)
        self.assertEqual(doc["status"],"UNRESOLVED")
        self.assertIsNone(doc["selected_frame_id"])
    def test_qwen_no_and_uncertain_never_authorize_visual(self):
        for answer in ["NO","UNCERTAIN"]:
            with self.subTest(answer=answer):
                doc=select_visual_shot(SHA,claim(),candidates(),[decision(answer=answer)],100.)
                self.assertEqual(doc["status"],"UNRESOLVED")
    def test_qwen_yes_to_different_words_must_not_authorize_claim(self):
        wrong=decision();wrong["claim_text_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"claim"):
            select_visual_shot(SHA,claim(),candidates(),[wrong],100.)
    def test_qwen_report_cannot_claim_human_approval(self):
        forged=decision();forged["human_approved"]=True
        with self.assertRaisesRegex(ValueError,"approval"):
            select_visual_shot(SHA,claim(),candidates(),[forged],100.)
    def test_textual_false_human_approval_label_is_rejected(self):
        false=decision();false["human_approved"]="true"
        with self.assertRaisesRegex(ValueError,"approval"):
            select_visual_shot(SHA,claim(),candidates(),[false],100.)
    def test_verifier_frame_sha_does_not_match_candidate(self):
        with self.assertRaisesRegex(ValueError,"frame"):
            select_visual_shot(SHA,claim(),candidates(),[decision(sha=F1)],100.)
    def test_forged_film_sha_rejected(self):
        with self.assertRaisesRegex(ValueError,"source"):
            select_visual_shot(SHA,claim(),candidates(),[decision(source="0"*64)],100.)
    def test_motion_statement_never_proven_by_one_still(self):
        doc=select_visual_shot(SHA,claim(motion=True),candidates(),[decision()],100.)
        self.assertEqual(doc["status"],"UNRESOLVED")
    def test_dialogue_cannot_be_visual_just_from_clip(self):
        doc=select_visual_shot(SHA,claim(verdict="DIALOGUE_SUPPORTED"),candidates(),[decision()],100.)
        self.assertEqual(doc["status"],"DIALOGUE_ONLY")
        self.assertIsNone(doc["selected_frame_id"])
    def test_candidate_out_of_movie_bounds_rejected(self):
        rows=candidates();rows[1]["end_s"]=10000.
        with self.assertRaisesRegex(ValueError,"time"):
            select_visual_shot(SHA,claim(),rows,[decision()],100.)
    def test_qwen_yes_without_original_claim_frame_cannot_swap_scene(self):
        doc=select_visual_shot(SHA,claim(),candidates(),[decision("V1","YES",sha=F1)],100.)
        self.assertEqual(doc["status"],"UNRESOLVED")
        self.assertIsNone(doc["selected_frame_id"])
if __name__=="__main__":unittest.main()
