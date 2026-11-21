"""Stage-3 integration contracts. Uses generated synthetic media only."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"skills"/"film-review-orchestrator"/"scripts"))
import jobctl
from stage3.framework import StageContext, run_stage
from stage3.media import probe, decode, scene_index
from stage3.providers import verify_provider_config

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Phase3Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg=os.environ.get("FRA_FFMPEG","ffmpeg")
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/"source.mp4"
        cp=subprocess.run([self.ffmpeg,"-nostdin","-v","error",
            "-f","lavfi","-i","color=c=blue:s=160x90:r=12:d=1.4",
            "-f","lavfi","-i","sine=frequency=440:duration=1.4",
            "-shortest","-c:v","mpeg4","-c:a","aac","-y",str(self.source)],
            capture_output=True,timeout=30)
        self.assertEqual(cp.returncode,0,cp.stderr.decode(errors="replace"))
        self.job=jobctl.create_job(self.source,self.root/"jobs","synthetic-unit",probe=False)
    def env(self,stage):
        output=self.job/".engine21"/"attempts"/stage/"0001"
        output.mkdir(parents=True,exist_ok=True)
        from engine21 import state
        return {
            "FRA_JOB":str(self.job),"FRA_STAGE":stage,
            "FRA_OUTPUT_DIR":str(output),"FRA_SOURCE":str(self.source),
            "FRA_SOURCE_SHA256":digest(self.source),
            "FRA_REQUIRED_OUTPUTS":json.dumps(state.REQUIRED_OUTPUTS[stage]),
            "FRA_REQUIRED_CHECKS":json.dumps(state.CHECKS[stage]),
        }
    def test_package_runtime_digest_is_available_for_host_pinning(self):
        from stage3.framework import runtime_digest
        self.assertRegex(runtime_digest(),r"^[0-9a-f]{64}$")
    def test_cli_rejects_mismatching_runtime_package_digest(self):
        e=self.env("N00")
        command=[sys.executable,"-B",str(ROOT/"stage3_adapter.py"),
            "--mode","synthetic","--runtime-sha256","0"*64]
        process=subprocess.run(command,env={**os.environ,**e},cwd=ROOT,
            capture_output=True,text=True,timeout=20)
        self.assertNotEqual(process.returncode,0)
        self.assertFalse((Path(e["FRA_OUTPUT_DIR"])/"evidence.json").exists())
    def test_framework_rejects_wrong_source_checksum(self):
        e=self.env("N00");e["FRA_SOURCE_SHA256"]="0"*64
        with self.assertRaises(ValueError):
            StageContext.from_env(e)
    def test_framework_rejects_output_outside_attempt(self):
        e=self.env("N00");e["FRA_OUTPUT_DIR"]=str(self.root/"wrong")
        with self.assertRaises(ValueError):
            StageContext.from_env(e)
    def test_framework_produces_sha_bound_evidence(self):
        e=self.env("N00")
        result=run_stage(mode="synthetic",environ=e)
        self.assertEqual(result["stage"],"N00")
        doc=json.loads((Path(e["FRA_OUTPUT_DIR"])/"evidence.json").read_text())
        self.assertTrue(doc["synthetic_fixture"])
        self.assertEqual(doc["source_sha256"],digest(self.source))
        manifest=json.loads((Path(e["FRA_OUTPUT_DIR"])/"source_manifest.json").read_text())
        self.assertTrue(manifest["synthetic_fixture"])
        self.assertTrue(all((self.job/x["path"]).is_file() for x in doc["artifacts"]))
    def test_real_ffprobe_and_scene_coverage(self):
        p=probe(self.source)
        self.assertGreater(p["duration_s"],1)
        self.assertIn("video",p["stream_types"])
        self.assertIn("audio",p["stream_types"])
        decode(self.source,need_audio=True,need_video=True)
        scenes,frames=scene_index(self.source,p["duration_s"])
        self.assertTrue(scenes)
        self.assertEqual(scenes[0]["start_s"],0)
        self.assertAlmostEqual(scenes[-1]["end_s"],p["duration_s"],places=2)
        self.assertEqual(len(scenes),len(frames))
    def test_synthetic_n01_outputs_are_time_valid(self):
        e=self.env("N01");run_stage(mode="synthetic",environ=e)
        out=Path(e["FRA_OUTPUT_DIR"])
        scenes=[json.loads(x) for x in (out/"scenes.jsonl").read_text().splitlines()]
        self.assertTrue(scenes)
        self.assertEqual(scenes[0]["start_s"],0)
    def test_missing_real_whisper_provider_fails_closed(self):
        e=self.env("N02")
        with self.assertRaises((ValueError,RuntimeError)):
            run_stage(mode="production",environ=e)
        self.assertFalse((Path(e["FRA_OUTPUT_DIR"])/"evidence.json").exists())
    def test_missing_real_qwen_or_clip_fails_closed(self):
        for stage in ("N03","N07"):
            e=self.env(stage)
            with self.assertRaises((ValueError,RuntimeError)):
                run_stage(mode="production",environ=e)
    def test_real_render_without_approved_edit_worker_is_blocked(self):
        run_stage(mode="synthetic",environ=self.env("N06"))
        run_stage(mode="synthetic",environ=self.env("N07"))
        for stage in ("N08","N09"):
            e=self.env(stage)
            if stage=="N09":
                # A fixture pilot exists, so production must not accept copying it.
                run_stage(mode="synthetic",environ=self.env("N08"))
            with self.assertRaises((RuntimeError,ValueError)):
                run_stage(mode="production",environ=e)
            self.assertFalse((Path(e["FRA_OUTPUT_DIR"])/"evidence.json").exists())
    def test_provider_config_requires_pinned_worker_files(self):
        config=self.root/"unprotected-worker.json"
        config.write_text(json.dumps({"schema_version":"3.0",
            "stages":{"N02":{"executable":sys.executable,
               "argv":["some-unknown-worker.py"],
               "executable_sha256":digest(sys.executable),
               "timeout_seconds":10,"input_files":{}}}}))
        with self.assertRaises(ValueError):
            verify_provider_config(config)
    def test_production_pilot_must_match_preapproved_preview(self):
        e=self.env("N08")
        # A trusted adapter cannot quietly substitute a different edited pilot.
        approved=self.job/"edit"/"pilot.mp4"
        approved.parent.mkdir(exist_ok=True)
        red=subprocess.run([self.ffmpeg,"-nostdin","-v","error",
          "-f","lavfi","-i","color=c=red:s=160x90:r=12:d=1.4",
          "-f","lavfi","-i","sine=frequency=660:duration=1.4",
          "-shortest","-c:v","mpeg4","-c:a","aac","-y",str(approved)],
          capture_output=True,timeout=30)
        self.assertEqual(red.returncode,0)
        worker=self.root/"custom_worker.py"
        worker.write_text(
          "import os,json,hashlib,shutil\nfrom pathlib import Path\n"
          "o=Path(os.environ['FRA_OUTPUT_DIR']);"
          "shutil.copy2(os.environ['FRA_SOURCE'],o/'pilot.mp4');"
          "(o/'timeline.json').write_text('{}');"
          "v={'stage':'N08','model_id':'LOCAL_EDITOR_TEST_ONLY',"
          "'synthetic_fixture':False,"
          "'source_sha256':os.environ['FRA_SOURCE_SHA256'],"
          "'checks':{k:True for k in json.loads(os.environ['FRA_REQUIRED_CHECKS'])}};"
          "(o/'provider_verification.json').write_text(json.dumps(v))\n")
        config=self.root/"pinned_worker.json"
        config.write_text(json.dumps({"schema_version":"3.0","stages":{
          "N08":{"executable":sys.executable,"argv":[str(worker)],
                 "executable_sha256":digest(sys.executable),
                 "timeout_seconds":20,
                 "input_files":{str(worker):digest(worker)}}}}))
        from unittest.mock import patch
        with patch.dict(os.environ,e):
            with self.assertRaises(ValueError):
                run_stage(mode="production",environ=e,provider_config=config)
        self.assertFalse((Path(e["FRA_OUTPUT_DIR"])/"evidence.json").exists())
    def test_provider_contract_rejects_nonabsolute_executable(self):
        config=self.root/"badprovider.json"
        config.write_text(json.dumps({"schema_version":"3.0",
            "stages":{"N02":{"executable":"python","argv":["test"],
                "executable_sha256":"0"*64,"timeout_seconds":15}}}))
        with self.assertRaises(ValueError):
            verify_provider_config(config)
    def test_synthetic_transcript_story_and_review(self):
        for stage in ("N02","N03","N04","N05"):
            e=self.env(stage);run_stage(mode="synthetic",environ=e)
            doc=json.loads((Path(e["FRA_OUTPUT_DIR"])/"evidence.json").read_text())
            self.assertEqual({Path(a["path"]).name for a in doc["artifacts"]},
                 set(json.loads(e["FRA_REQUIRED_OUTPUTS"])))
        review=(self.job/".engine21"/"attempts"/"N05"/"0001"/"review_final.txt").read_text(encoding="utf8")
        self.assertIn("tổng hợp",review.lower())
    def test_synthetic_voice_and_semantic_map(self):
        e=self.env("N06");run_stage(mode="synthetic",environ=e)
        wav=Path(e["FRA_OUTPUT_DIR"])/"narration.wav"
        decode(wav,need_audio=True)
        e=self.env("N07");run_stage(mode="synthetic",environ=e)
        doc=json.loads((Path(e["FRA_OUTPUT_DIR"])/"sentence_shot_map.json").read_text())
        self.assertEqual(doc["source_movie_sha256"],digest(self.source))
        self.assertTrue(doc["sentences"])
        self.assertEqual(doc["sentences"][0]["chosen_shots"][0]["verdict"],"CONTEXT_ONLY")
    def test_synthetic_render_pilot_and_final(self):
        e=self.env("N06");run_stage(mode="synthetic",environ=e)
        e=self.env("N07");run_stage(mode="synthetic",environ=e)
        e=self.env("N08");run_stage(mode="synthetic",environ=e)
        pilot=Path(e["FRA_OUTPUT_DIR"])/"pilot.mp4"
        decode(pilot,need_audio=True,need_video=True)
        e=self.env("N09");run_stage(mode="synthetic",environ=e)
        final=Path(e["FRA_OUTPUT_DIR"])/"final_review.mp4"
        decode(final,need_audio=True,need_video=True)
        self.assertGreater(final.stat().st_size,1000)

if __name__=="__main__":
    unittest.main()
