"""Detect shot *candidates* inside authorized excerpts, no false story truth."""
import hashlib,unittest
from stage6.scene_proposals import build_scene_proposals
SHA=hashlib.sha256(b"source").hexdigest()
def windows():
    return [{"sample_id":"F01","original_start_s":100.,"original_end_s":130.},
      {"sample_id":"F02","original_start_s":200.,"original_end_s":230.}]
class SceneProposalsTests(unittest.TestCase):
    def test_relative_cuts_map_to_movie_times_and_all_segments_remain_pending(self):
        doc=build_scene_proposals(SHA,300.,windows(),{"F01":[5.,10.],"F02":[]})
        self.assertEqual(len(doc["scenes"]),4)
        self.assertEqual([v["source_interval_s"] for v in doc["scenes"][:3]],
                          [[100.,105.],[105.,110.],[110.,130.]])
        self.assertEqual(doc["scenes"][3]["source_interval_s"],[200.,230.])
        self.assertEqual(doc["scenes"][1]["source_sample_id"],"F01")
        self.assertTrue(all(v["status"]=="AUTO_SCENE_CANDIDATE_PENDING_VIDEO_REVIEW" for v in doc["scenes"]))
        self.assertFalse(doc["real_movie_actions_certified"])
    def test_no_scene_cuts_still_unconfirmed_full_window(self):
        doc=build_scene_proposals(SHA,300.,windows(),{"F01":[],"F02":[]})
        self.assertEqual(len(doc["scenes"]),2)
        self.assertTrue(all(v["human_review_required"] for v in doc["scenes"]))
    def test_outside_window_cut_rejected(self):
        for bad in (-1.,0.,30.,31.):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,"cut"):
                    build_scene_proposals(SHA,300.,windows(),{"F01":[bad],"F02":[]})
    def test_duplicate_nonfinite_cut_or_unsorted_rejected(self):
        for cuts in ([3.,3.],[10.,4.],[float("nan")]):
            with self.subTest(cuts=cuts):
                with self.assertRaises(ValueError):
                    build_scene_proposals(SHA,300.,windows(),{"F01":cuts,"F02":[]})
    def test_missing_or_extra_sample_ids_rejected(self):
        for payload in ({"F01":[]},{"F01":[],"F02":[],"FAKE":[2.]}):
            with self.assertRaisesRegex(ValueError,"sample"):
                build_scene_proposals(SHA,300.,windows(),payload)
    def test_window_outside_original_movie_or_overlap_rejected(self):
        w=windows();w[0]["original_end_s"]=340.
        with self.assertRaisesRegex(ValueError,"window"):
            build_scene_proposals(SHA,300.,w,{"F01":[],"F02":[]})
        w=windows();w[1]["original_start_s"]=120.
        with self.assertRaisesRegex(ValueError,"overlap"):
            build_scene_proposals(SHA,300.,w,{"F01":[],"F02":[]})
if __name__=="__main__":unittest.main()
