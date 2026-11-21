"""No movie recap/voice/pilot approved by linking a still frame and a Qwen YES."""
import hashlib,unittest
from stage6.review_packet import build_review_packet
SHA=hashlib.sha256(b"test film").hexdigest()
def fixture():
    catalog={
      "V1":{"kind":"visual","text":"Person stands by a van.","source_sha256":SHA,"start_s":15.,"end_s":15.2},
      "V2":{"kind":"visual","text":"Person stands in a dim room.","source_sha256":SHA,"start_s":45.,"end_s":45.2}}
    storyboard={"source_sha256":SHA,"ready_to_render":False,
      "shots":[{"sentence_id":"S01","claim_id":"C01","review_text":"Có người đứng cạnh xe.",
         "source_sha256":SHA,"source_evidence_id":"V1","source_interval_s":[15.,15.2],
         "model_source_visual_verification":"QWEN_TENTATIVE_NOT_HUMAN"},
        {"sentence_id":"S02","claim_id":"C02","review_text":"Một người đứng trong căn phòng tối.",
         "source_sha256":SHA,"source_evidence_id":"V2","source_interval_s":[45.,45.2],
         "model_source_visual_verification":"QWEN_TENTATIVE_NOT_HUMAN"}]}
    scenes={"source_sha256":SHA,"scenes":[
       {"scene_id":"SHOT_F1_001","source_interval_s":[10.,20.],"source_sample_id":"F01",
        "status":"AUTO_SCENE_CANDIDATE_PENDING_VIDEO_REVIEW"},
       {"scene_id":"SHOT_F2_001","source_interval_s":[40.,50.],"source_sample_id":"F02",
        "status":"AUTO_SCENE_CANDIDATE_PENDING_VIDEO_REVIEW"}]}
    dialog={"source_sha256":SHA,"rows":[{"id":"A1","source_sha256":SHA,"review_status":"PENDING_HUMAN_LISTEN"}],
      "script_or_voice_approved":False}
    return storyboard,catalog,scenes,dialog
class PacketTests(unittest.TestCase):
    def test_source_claims_preserved_and_every_decision_remains_pending(self):
        sb,cat,sc,di=fixture()
        result=build_review_packet(SHA,sb,cat,sc,di)
        self.assertEqual([r["claim_id"] for r in result["visual_claims"]],["C01","C02"])
        self.assertEqual([r["scene_id"] for r in result["visual_claims"]],["SHOT_F1_001","SHOT_F2_001"])
        self.assertTrue(all(r["review_status"]=="PENDING_HUMAN_VIDEO_REVIEW" for r in result["visual_claims"]))
        self.assertEqual(result["pending_audio_count"],1)
        self.assertEqual(result["review_gates"],{"script":"PENDING","voice":"PENDING","pilot":"PENDING"})
        self.assertFalse(result["can_render"])
        self.assertFalse(result["can_tts"])
        self.assertFalse(result["signed_by_human"])
    def test_changed_frame_or_mismatched_sha_rejected(self):
        sb,cat,sc,di=fixture();sb["shots"][0]["source_evidence_id"]="UNKNOWN"
        with self.assertRaisesRegex(ValueError,"evidence"):
            build_review_packet(SHA,sb,cat,sc,di)
        sb,cat,sc,di=fixture();cat["V1"]["source_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"source"):
            build_review_packet(SHA,sb,cat,sc,di)
    def test_frame_outside_any_scene_is_not_accepted(self):
        sb,cat,sc,di=fixture();sc["scenes"][0]["source_interval_s"]=[10.,11.]
        with self.assertRaisesRegex(ValueError,"scene"):
            build_review_packet(SHA,sb,cat,sc,di)
    def test_source_frame_straddling_two_detected_cuts_is_ambiguous_not_auto_accepted(self):
        sb,cat,sc,di=fixture()
        sc["scenes"]=[{"scene_id":"SHOT_F1_001","source_interval_s":[10.,15.05],
            "source_sample_id":"F01","status":"AUTO_SCENE_CANDIDATE_PENDING_VIDEO_REVIEW"},
            {"scene_id":"SHOT_F1_002","source_interval_s":[15.05,20.],
             "source_sample_id":"F01","status":"AUTO_SCENE_CANDIDATE_PENDING_VIDEO_REVIEW"},
            sc["scenes"][1]]
        packet=build_review_packet(SHA,sb,cat,sc,di)
        row=packet["visual_claims"][0]
        self.assertEqual(row["review_status"],"PENDING_HUMAN_CUT_BOUNDARY_REVIEW")
        self.assertIsNone(row["scene_id"])
        self.assertEqual(row["candidate_scene_ids"],["SHOT_F1_001","SHOT_F1_002"])
        self.assertFalse(packet["can_render"])
    def test_fake_render_or_spoofed_approval_blocked(self):
        sb,cat,sc,di=fixture();sb["ready_to_render"]=True
        with self.assertRaisesRegex(ValueError,"approval"):
            build_review_packet(SHA,sb,cat,sc,di)
        sb,cat,sc,di=fixture();di["script_or_voice_approved"]=True
        with self.assertRaisesRegex(ValueError,"approval"):
            build_review_packet(SHA,sb,cat,sc,di)
    def test_claim_of_unseen_action_blocked_in_script_candidate(self):
        sb,cat,sc,di=fixture();sb["shots"][0]["review_text"]="Anh ấy đã bắn chết ai đó."
        with self.assertRaisesRegex(ValueError,"action"):
            build_review_packet(SHA,sb,cat,sc,di)
    def test_missing_or_duplicate_claim_ids_rejected(self):
        sb,cat,sc,di=fixture();sb["shots"][1]["claim_id"]="C01"
        with self.assertRaisesRegex(ValueError,"duplicate"):
            build_review_packet(SHA,sb,cat,sc,di)
if __name__=="__main__":unittest.main()
