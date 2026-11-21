"""A synthetic QA pilot must preserve every spoken second, never truncate TTS."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from stage4.media import loop_source_with_voice
from stage3.media import decode

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Phase4SyntheticMediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p=Path(self.tmp.name)
        self.video=p/"short.mp4";self.wav=p/"long.wav";self.output=p/"pilot.mp4"
        c=subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
          "-i","color=c=red:s=128x72:r=12:d=0.6",
          "-f","lavfi","-i","sine=frequency=440:duration=0.6",
          "-shortest","-c:v","mpeg4","-c:a","aac","-y",str(self.video)],
          capture_output=True,timeout=20)
        if c.returncode:raise unittest.SkipTest("FFmpeg unavailable")
        c=subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
          "-i","sine=frequency=530:duration=2.0","-c:a","pcm_s16le",
          "-y",str(self.wav)],capture_output=True,timeout=20)
        self.assertEqual(c.returncode,0)
    def test_looping_short_visual_preserves_entire_voice(self):
        before=sha(self.video)
        result=loop_source_with_voice(self.video,self.wav,self.output)
        self.assertTrue(result["synthetic_loop"])
        props=decode(self.output,need_audio=True,need_video=True)
        self.assertGreaterEqual(props["duration_s"],1.94)
        self.assertLess(props["duration_s"],2.12)
        self.assertEqual(before,sha(self.video))
    def test_does_not_overwrite_existing_pilot(self):
        self.output.write_bytes(b"DO_NOT_OVERWRITE")
        with self.assertRaises(FileExistsError):
            loop_source_with_voice(self.video,self.wav,self.output)
        self.assertEqual(self.output.read_bytes(),b"DO_NOT_OVERWRITE")
if __name__=="__main__":
    unittest.main()
