"""Bilingual manifest must never rewrite source English or self-approve."""
import hashlib
import unittest
from stage5.translation import build_translation_pack
SHA=hashlib.sha256(b"film source").hexdigest()

def asr(id="A1",text="Letters to Santa?",sha=SHA,start=10.,end=12.,logprob=-0.1):
    return {"id":id,"text":text,"start_s":start,"end_s":end,"source_sha256":sha,
            "original_spoken_language":"en","avg_logprob":logprob}
def proposal(id="A1",english="Letters to Santa?",vi="Thư gửi ông già Noel?"):
    return {"evidence_id":id,"english_text_sha256":hashlib.sha256(english.encode("utf8")).hexdigest(),
            "translation_vi":vi,"model_id":"offline-qa-qwen","human_approved":False}
class TranslationTests(unittest.TestCase):
    def test_bilingual_candidate_keeps_raw_english_source_and_timecode(self):
        doc=build_translation_pack([asr()],SHA,30.,[proposal()])
        row=doc["rows"][0]
        self.assertEqual(row["original_english"],"Letters to Santa?")
        self.assertEqual(row["translation_vi_candidate"],"Thư gửi ông già Noel?")
        self.assertEqual(row["id"],"A1")
        self.assertEqual((row["start_s"],row["end_s"]),(10.,12.))
        self.assertEqual(row["status"],"TRANSLATION_PENDING_HUMAN_REVIEW")
        self.assertFalse(row["human_approved"])
        self.assertFalse(doc["translation_semantics_certified"])
    def test_no_translation_is_not_english_disguised_as_vietnamese(self):
        doc=build_translation_pack([asr()],SHA,30.)
        self.assertIsNone(doc["rows"][0]["translation_vi_candidate"])
    def test_weak_asr_requires_listening_even_if_model_translates(self):
        doc=build_translation_pack([asr(logprob=-0.418)],SHA,30.,[proposal()])
        self.assertEqual(doc["rows"][0]["asr_risk"],"NEEDS_AUDIO_LISTENING")
    def test_english_text_changed_invalidates_candidate_hash(self):
        doc=build_translation_pack([asr(text="Actual different English")],SHA,30.,[proposal()])
        self.assertIsNone(doc["rows"][0]["translation_vi_candidate"])
        self.assertEqual(len(doc["quarantined"]),1)
    def test_wrong_film_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"source"):
            build_translation_pack([asr(sha="0"*64)],SHA,30.)
    def test_bad_time_or_duplicate_ids_rejected(self):
        with self.assertRaisesRegex(ValueError,"time"):
            build_translation_pack([asr(end=40.)],SHA,30.)
        with self.assertRaisesRegex(ValueError,"duplicate"):
            build_translation_pack([asr(),asr()],SHA,30.)
    def test_model_cannot_claim_human_approval(self):
        proposed=proposal();proposed["human_approved"]=True
        doc=build_translation_pack([asr()],SHA,30.,[proposed])
        self.assertIsNone(doc["rows"][0]["translation_vi_candidate"])
        self.assertEqual(len(doc["quarantined"]),1)
    def test_unhashable_model_evidence_id_is_quarantined_not_crash(self):
        bad=proposal();bad["evidence_id"]=["A1"]
        pack=build_translation_pack([asr()],SHA,30.,[bad])
        self.assertEqual(len(pack["quarantined"]),1)
        self.assertIsNone(pack["rows"][0]["translation_vi_candidate"])
    def test_duplicate_candidate_translation_is_quarantined(self):
        doc=build_translation_pack([asr()],SHA,30.,[proposal(),proposal()])
        self.assertEqual(len(doc["quarantined"]),2)
        self.assertIsNone(doc["rows"][0]["translation_vi_candidate"])
if __name__=="__main__":unittest.main()
