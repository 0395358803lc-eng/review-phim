"""Phase6 never substitutes an ASR translation for heard English dialogue."""
import hashlib
import unittest
from stage6.dialogue_review import build_dialogue_review_queue

SHA=hashlib.sha256(b"real movie fixture").hexdigest()
def asr(id="A01",text="Where did the letters to Santa go?",a=102.,b=104.,prob=-0.2):
    return {"id":id,"text":text,"start_s":a,"end_s":b,
            "avg_logprob":prob,"source_sha256":SHA,"original_spoken_language":"en"}
def row(record, vi="Những chữ cái gửi ông già Noel ở đâu?"):
    return {"id":record["id"],"start_s":record["start_s"],"end_s":record["end_s"],
            "source_sha256":SHA,"original_english":record["text"],
            "original_text_sha256":hashlib.sha256(record["text"].encode("utf8")).hexdigest(),
            "asr_risk":"UNVERIFIED_ASR","avg_logprob":record["avg_logprob"],
            "translation_vi_candidate":vi,"human_approved":False}
def fixture():
    original=[asr(),asr(id="A02",text="I didn't see the letter.",a=129.,b=129.9,prob=-0.41)]
    trans={"movie_source_sha256":SHA,"rows":[row(x) for x in original],
           "translation_semantics_certified":False}
    windows=[{"sample_id":"F02","original_start_s":100.,"original_end_s":130.}]
    return trans,original,windows
class DialogueReviewTests(unittest.TestCase):
    def test_source_and_translation_pending_with_audio_preview_and_flagged_mistranslation(self):
        trans,src,windows=fixture()
        pack=build_dialogue_review_queue(trans,src,SHA,200.,windows)
        self.assertEqual(len(pack["rows"]),2)
        self.assertEqual(pack["rows"][0]["id"],"A01")
        self.assertEqual(pack["rows"][0]["original_english"],src[0]["text"])
        self.assertEqual(pack["rows"][0]["priority"],"CHECK_TRANSLATION_MEANING")
        self.assertIn("MAIL_LETTERS_FALSE_FRIEND",pack["rows"][0]["risk_flags"])
        self.assertFalse(pack["rows"][0]["transcript_confirmed"])
        self.assertFalse(pack["rows"][0]["translation_confirmed"])
        self.assertEqual(pack["rows"][0]["review_status"],"PENDING_HUMAN_LISTEN")
        self.assertEqual(pack["rows"][1]["priority"],"CHECK_AUDIO_FIRST")
        self.assertLessEqual(pack["rows"][1]["preview_end_s"],130.)
        self.assertFalse(pack["script_or_voice_approved"])
    def test_changed_english_word_hash_fails_closed(self):
        trans,src,w=fixture();trans["rows"][0]["original_english"]="Different dialogue"
        with self.assertRaisesRegex(ValueError,"English"):
            build_dialogue_review_queue(trans,src,SHA,200.,w)
    def test_missing_or_duplicate_asr_ids_fail(self):
        trans,src,w=fixture();trans["rows"].pop()
        with self.assertRaisesRegex(ValueError,"ASR"):
            build_dialogue_review_queue(trans,src,SHA,200.,w)
        trans,src,w=fixture();trans["rows"].append(trans["rows"][0])
        with self.assertRaisesRegex(ValueError,"duplicate"):
            build_dialogue_review_queue(trans,src,SHA,200.,w)
    def test_other_movie_or_invalid_time_fails(self):
        trans,src,w=fixture();trans["rows"][0]["source_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"source"):
            build_dialogue_review_queue(trans,src,SHA,200.,w)
        trans,src,w=fixture();trans["rows"][0]["end_s"]=250.
        with self.assertRaisesRegex(ValueError,"time"):
            build_dialogue_review_queue(trans,src,SHA,200.,w)
    def test_forged_human_translation_approval_is_rejected(self):
        trans,src,w=fixture();trans["rows"][0]["human_approved"]=True
        with self.assertRaisesRegex(ValueError,"approval"):
            build_dialogue_review_queue(trans,src,SHA,200.,w)
    def test_asr_outside_authorized_sample_window_is_rejected(self):
        trans,src,w=fixture();src[0]["start_s"]=88.;trans["rows"][0]["start_s"]=88.
        with self.assertRaisesRegex(ValueError,"window"):
            build_dialogue_review_queue(trans,src,SHA,200.,w)
    def test_translation_non_text_does_not_create_approved_content(self):
        trans,src,w=fixture();trans["rows"][0]["translation_vi_candidate"]=None
        pack=build_dialogue_review_queue(trans,src,SHA,200.,w)
        self.assertIn("MISSING_TRANSLATION",pack["rows"][0]["risk_flags"])
        self.assertIsNone(pack["rows"][0]["translation_vi_candidate"])
if __name__=="__main__":unittest.main()
