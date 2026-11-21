"""Offline reviewer HTML must be safe to view and never mark approvals."""
import unittest
from stage6.offline_html import render_review_html
SHA="a"*64
class OfflineHtmlTests(unittest.TestCase):
    def test_escapes_untrusted_asr_and_review_content_and_marks_unsigned(self):
        queue={"source_sha256":SHA,"rows":[{
         "id":"A01","original_english":"<img src=x onerror=alert(1)>",
         "translation_vi_candidate":"<script>alert('x')</script>",
         "source_sample_id":"F01","start_s":10.,"end_s":11.,
         "preview_start_s":9.5,"preview_end_s":11.5,
         "priority":"CHECK_AUDIO_FIRST","risk_flags":["LOW_ASR_CONFIDENCE_LISTEN"]}]}
        packet={"source_sha256":SHA,"visual_claims":[{
          "sentence_id":"S01","claim_id":"C01","source_evidence_id":"V_F01_05",
          "scene_sample_id":"F01","scene_id":"SHOT_F01_001",
          "review_vi_candidate":"<b>Model candidate</b>",
          "source_frame_observation":"Original <danger> caption",
          "scene_interval_s":[10.,12.]}]}
        html=render_review_html(queue,packet,{"F01":"file:///D:/Private/F01.mp4"},
            {"V_F01_05":"file:///D:/Private/F01_05.jpg"})
        self.assertIn("UNSIGNED",html)
        self.assertIn("PENDING",html)
        self.assertIn("&lt;img src=x",html)
        self.assertIn("&lt;script&gt;",html)
        self.assertNotIn("<script>alert('x')</script>",html)
        self.assertNotIn("<b>Model candidate</b>",html)
        self.assertIn("Export",html)
    def test_cut_boundary_ambiguity_is_clearly_labeled_to_reviewer(self):
        queue={"source_sha256":SHA,"rows":[]}
        packet={"source_sha256":SHA,"visual_claims":[{
          "sentence_id":"S01","claim_id":"C01","source_evidence_id":"V_F01_05",
          "scene_sample_id":"F01","scene_id":None,
          "candidate_scene_ids":["SHOT_F01_002","SHOT_F01_003"],
          "review_status":"PENDING_HUMAN_CUT_BOUNDARY_REVIEW",
          "review_vi_candidate":"Một người đứng bên xe.",
          "scene_interval_s":[543.333,548.25]}]}
        html=render_review_html(queue,packet,{"F01":"file:///D:/Private/F01.mp4"},{})
        self.assertIn("PENDING_HUMAN_CUT_BOUNDARY_REVIEW",html)
        self.assertIn("SHOT_F01_002",html)
        self.assertIn("SHOT_F01_003",html)
    def test_missing_source_clip_refuses_unsafe_partial_page(self):
        q={"source_sha256":SHA,"rows":[{"id":"A01","source_sample_id":"F01",
             "original_english":"Hello","translation_vi_candidate":"Chào",
             "start_s":1,"end_s":2,"priority":"NORMAL_HUMAN_REVIEW","risk_flags":[]}]}
        p={"source_sha256":SHA,"visual_claims":[]}
        with self.assertRaisesRegex(ValueError,"source clip"):
            render_review_html(q,p,{}, {})
if __name__=="__main__":unittest.main()
