"""Phase 4 evidence-first review: 100% synthetic manifest fixtures."""
import hashlib
import unittest
from stage4.evidence import build_timeline
from stage4.review import build_review

SHA=hashlib.sha256(b"generated-synthetic-source").hexdigest()

def vision(i,start,end,text,sha=SHA):
    return {"id":i,"start_s":start,"end_s":end,"description":text,"source_sha256":sha}

def speech(i,start,end,text,sha=SHA):
    return {"id":i,"start_s":start,"end_s":end,"text":text,"source_sha256":sha}

class GroundedTimelineTests(unittest.TestCase):
    def setUp(self):
        self.vis=[vision("V1",0,2,"A red square and blue circle."),
                  vision("V2",2,3.5,"A green triangle.")]
        self.asr=[speech("A1",0.2,1.7,"Đây là hình vuông đỏ."),
                  speech("A2",4,5,"Tôi không nhìn thấy gì.")]
    def timeline(self):
        return build_timeline(self.asr,self.vis,SHA,5.5)
    def test_multiple_events_have_source_bounds_and_unmatched_asr(self):
        result=self.timeline()
        self.assertEqual(len(result["events"]),3)
        self.assertEqual(result["events"][0]["visual_evidence_ids"],["V1"])
        self.assertEqual(result["events"][0]["asr_evidence_ids"],["A1"])
        self.assertEqual(result["events"][-1]["asr_evidence_ids"],["A2"])
        self.assertEqual(result["events"][-1]["visual_evidence_ids"],[])
        self.assertEqual(result["source_sha256"],SHA)
        self.assertEqual(set(result["catalog"]),{"V1","V2","A1","A2"})
    def test_same_id_across_modalities_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            build_timeline([speech("V1",0,1,"X")],self.vis,SHA,5.5)
    def test_wrong_source_checksum_rejected(self):
        bad=[vision("V1",0,2,"A red square.","f"*64)]
        with self.assertRaisesRegex(ValueError,"source"):
            build_timeline([],bad,SHA,5.5)
    def test_out_of_range_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError,"time"):
            build_timeline([], [vision("V",0,6,"Out of range")],SHA,5.5)
    def test_overlapping_conflicting_captions_flagged(self):
        visual=[vision("V1",0,2,"A red box"),vision("V2",0,2,"A blue box")]
        timeline=build_timeline([],visual,SHA,3)
        self.assertEqual(len(timeline["events"]),1)
        self.assertTrue(timeline["events"][0]["visual_conflict"])
        self.assertTrue(timeline["unresolved"])
    def test_no_source_observations_rejected(self):
        with self.assertRaisesRegex(ValueError,"empty"):
            build_timeline([],[],SHA,4)

class GroundedReviewTests(unittest.TestCase):
    def setUp(self):
        self.timeline=build_timeline(
            [speech("A1",0.3,1.2,"Đây là hình vuông đỏ."),
             speech("A2",4,5,"Không có ai ở đây.")],
            [vision("V1",0,2,"A red square and a blue circle."),
             vision("V2",2,3.5,"A green triangle.")],SHA,6)
    def test_multiple_sentence_review_has_per_claim_evidence(self):
        doc=build_review(self.timeline)
        self.assertGreaterEqual(len(doc["sentences"]),3)
        self.assertEqual(len(doc["evidence_ledger"]),sum(len(s["atomic_claims"]) for s in doc["sentences"]))
        catalog=set(self.timeline["catalog"])
        for sentence in doc["sentences"]:
            self.assertTrue(sentence["human_review_required"])
            for claim in sentence["atomic_claims"]:
                self.assertTrue(set(claim["evidence_ids"])<=catalog)
                self.assertIn(claim["verdict"],("VISUAL_DIRECT","DIALOGUE_SUPPORTED"))
                self.assertEqual(claim["source_sha256"],SHA)
        self.assertIn("A red square",doc["review_text"])
        self.assertIn("Đây là hình vuông đỏ.",doc["review_text"])
    def test_hallucinated_actor_and_usb_claim_is_quarantined(self):
        doc=build_review(self.timeline,proposals=[{"event_id":"EVT0001",
           "review_text":"Agus vừa đánh cắp USB của cô gái.",
           "claim_text":"Agus vừa đánh cắp USB của cô gái.",
           "evidence_ids":["V1"],"verdict":"VISUAL_DIRECT"}])
        self.assertEqual(len(doc["quarantined_proposals"]),1)
        self.assertNotIn("Agus",doc["review_text"])
    def test_forged_evidence_id_is_not_accepted(self):
        doc=build_review(self.timeline,proposals=[{"event_id":"EVT0001",
            "review_text":"Evidence says X","claim_text":"Evidence says X",
            "evidence_ids":["UNSEEN"],"verdict":"DIALOGUE_SUPPORTED"}])
        self.assertEqual(len(doc["quarantined_proposals"]),1)
    def test_extract_only_limited_sentences_does_not_make_up_remainder(self):
        doc=build_review(self.timeline,max_sentences=1)
        self.assertEqual(len(doc["sentences"]),1)
        self.assertTrue(doc["truncated"])
    def test_conflict_without_asr_does_not_produce_approved_draft(self):
        tl=build_timeline([], [vision("V1",0,1,"red square"),
              vision("V2",0,1,"blue square")],SHA,2)
        with self.assertRaisesRegex(ValueError,"grounded"):
            build_review(tl)
    def test_proposal_with_exact_source_quote_can_be_drafted_not_approved(self):
        doc=build_review(self.timeline,proposals=[{"event_id":"EVT0001",
            "review_text":"A red square and a blue circle.",
            "claim_text":"A red square and a blue circle.",
            "evidence_ids":["V1"],"verdict":"VISUAL_DIRECT"}])
        self.assertEqual(len(doc["quarantined_proposals"]),0)
        self.assertIn("A red square and a blue circle.",doc["review_text"])
        self.assertTrue(doc["human_approval_required"])

if __name__=="__main__":
    unittest.main()
