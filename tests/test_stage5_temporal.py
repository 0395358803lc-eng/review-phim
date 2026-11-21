"""Chronological frame evidence is model hypothesis, not film plot fact."""
import hashlib
import unittest
from stage5.temporal import build_temporal_pack
SHA=hashlib.sha256(b"source movie").hexdigest()
def frames():
    return [{"id":f"V{i}","frame_center_s":float(i),"source_sha256":SHA,
              "frame_sha256":str(i)*64,"description":f"Frame {i}: person in room"}
            for i in (5,6,7,8)]
class TemporalTests(unittest.TestCase):
    def test_ordered_frames_mark_motion_hypothesis_unverified(self):
        doc=build_temporal_pack(SHA,20.,frames(),"A person appears to turn around.")
        self.assertEqual(doc["frame_ids"],["V5","V6","V7","V8"])
        self.assertEqual(doc["temporal_statement_status"],"MODEL_HYPOTHESIS_NEEDS_HUMAN_VIDEO_REVIEW")
        self.assertFalse(doc["action_certified"])
    def test_unordered_frames_fails(self):
        r=frames();r[0],r[1]=r[1],r[0]
        with self.assertRaisesRegex(ValueError,"order"):
            build_temporal_pack(SHA,20.,r,"Somebody turns")
    def test_one_frame_cannot_prove_action(self):
        with self.assertRaisesRegex(ValueError,"two"):
            build_temporal_pack(SHA,20.,frames()[:1],"A person fires")
    def test_other_film_sha_rejected(self):
        r=frames();r[0]["source_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"source"):
            build_temporal_pack(SHA,20.,r,"A person moves")
if __name__=="__main__":unittest.main()
