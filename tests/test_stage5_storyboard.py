"""Plan multiple sentences using real original claim IDs. Never fake voice."""
import hashlib
import unittest
from stage5.storyboard import build_storyboard
SHA=hashlib.sha256(b"film source").hexdigest()
def fixture():
    catalog={
      "V1":{"kind":"visual","source_sha256":SHA,"start_s":10.,"end_s":10.2,"text":"Person near car"},
      "V2":{"kind":"visual","source_sha256":SHA,"start_s":20.,"end_s":20.2,"text":"Postal worker"},
      "V3":{"kind":"visual","source_sha256":SHA,"start_s":30.,"end_s":30.2,"text":"Person aiming rifle"}}
    sentences=[]
    selections={}
    for idx,eid in enumerate(["V1","V2","V3"],1):
        sid=f"S{idx:04d}"
        cid=f"C{idx:04d}"
        sentences.append({"sentence_id":sid,"review_text":f"Cảnh {idx}",
          "source_sha256":SHA,"atomic_claims":[{"claim_id":cid,
           "verdict":"VISUAL_DIRECT","evidence_ids":[eid],
           "text":catalog[eid]["text"],"source_sha256":SHA}]})
        selections[sid]={"status":"TENTATIVE_VISUAL_CANDIDATE","selected_frame_id":eid,
          "original_claim_id":cid,"source_sha256":SHA}
    return dict(source_sha256=SHA,source_duration_s=50.,sentences=sentences,
        catalog=catalog,selections=selections)
class StoryboardTests(unittest.TestCase):
    def test_three_sentences_keep_exact_original_claim_and_frame_ids(self):
        doc=build_storyboard(**fixture())
        self.assertEqual(len(doc["shots"]),3)
        self.assertEqual([x["claim_id"] for x in doc["shots"]],["C0001","C0002","C0003"])
        self.assertEqual([x["source_evidence_id"] for x in doc["shots"]],["V1","V2","V3"])
        self.assertFalse(doc["ready_to_render"])
        self.assertTrue(doc["voice_approval_required"])
        self.assertIsNone(doc["narration_duration_s"])
    def test_forged_claim_id_rejected(self):
        x=fixture();x["selections"]["S0002"]["original_claim_id"]="FAKE"
        with self.assertRaisesRegex(ValueError,"claim"):
            build_storyboard(**x)
    def test_unresolved_scene_refused(self):
        x=fixture();x["selections"]["S0003"]["status"]="UNRESOLVED"
        with self.assertRaisesRegex(ValueError,"unresolved"):
            build_storyboard(**x)
    def test_missing_scene_or_claim_rejected(self):
        x=fixture();x["selections"].pop("S0002")
        with self.assertRaisesRegex(ValueError,"sentence"):
            build_storyboard(**x)
    def test_malformed_source_evidence_range_rejected(self):
        x=fixture();x["catalog"]["V3"]["end_s"]=60.
        with self.assertRaisesRegex(ValueError,"time"):
            build_storyboard(**x)
    def test_optional_timeline_not_considered_approved(self):
        x=fixture();x["voice_timeline"]=[
          {"sentence_id":f"S{i:04d}","voice_start_s":i-1.,"voice_end_s":float(i)}
          for i in range(1,4)]
        doc=build_storyboard(**x)
        self.assertFalse(doc["ready_to_render"])
        self.assertEqual(doc["narration_duration_s"],3.)
    def test_unsupported_story_claim_refused_even_if_selection_yes(self):
        x=fixture();x["sentences"][0]["atomic_claims"][0]["verdict"]="UNRESOLVED"
        with self.assertRaises(ValueError):
            build_storyboard(**x)
if __name__=="__main__":unittest.main()
