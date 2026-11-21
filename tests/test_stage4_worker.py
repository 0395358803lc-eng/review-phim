"""N04-N05 QA worker must use real evidence, not hardcoded shape narrative."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from engine21 import state
from qa.legacy_offline_worker import WorkerContext,_n04,_n05

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class GroundedStageWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/"source.mp4"
        process=subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
            "-i","color=c=blue:s=160x90:r=12:d=4",
            "-f","lavfi","-i","sine=frequency=440:duration=4",
            "-shortest","-c:v","mpeg4","-c:a","aac","-y",str(self.source)],
            capture_output=True,timeout=35)
        if process.returncode:raise unittest.SkipTest("FFmpeg missing")
        self.hash=sha(self.source)
        self.job=self.root/"job"
        self.job.mkdir()
        self.manifest={"stages":{}}
        self.add_stage("N02",{"transcript_vi.jsonl": [
           {"id":"A1","start_s":0.2,"end_s":1.2,
            "text":"Đây là một ngôi sao màu vàng.","source_sha256":self.hash}]})
        self.add_stage("N03",{"visual_observations.jsonl":[
           {"id":"V1","start_s":0,"end_s":2,
            "description":"A yellow star.","source_sha256":self.hash},
           {"id":"V2","start_s":2,"end_s":4,
            "description":"A purple balloon.","source_sha256":self.hash}]})
        self.update_state()
    def update_state(self):
        root=self.job/".engine21"
        root.mkdir(exist_ok=True)
        (root/"state.json").write_text(json.dumps(self.manifest),encoding="utf8")
    def add_stage(self,stage,outputs):
        output=self.job/".engine21"/"attempts"/stage/"0001"
        output.mkdir(parents=True,exist_ok=True)
        artifacts=[]
        for name,rows in outputs.items():
            p=output/name
            if name.endswith(".jsonl"):
                p.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf8")
            else:
                p.write_text(json.dumps(rows,ensure_ascii=False),encoding="utf8")
            artifacts.append({"path":str(p.relative_to(self.job)),"sha256":sha(p)})
        self.manifest["stages"][stage]={"status":"DONE","artifacts":artifacts}
    def ctx(self,stage):
        out=self.job/".engine21"/"attempts"/stage/"0001"
        out.mkdir(parents=True,exist_ok=True)
        return WorkerContext(self.job,stage,self.source,out,self.hash,
                  state.REQUIRED_OUTPUTS[stage],state.CHECKS[stage])
    def test_multi_event_story_from_actual_evidence_and_qa_limited_draft(self):
        ctx4=self.ctx("N04")
        _n04(ctx4)
        story=json.loads((ctx4.out/"story_timeline.json").read_text(encoding="utf8"))
        self.assertEqual(len(story["events"]),2)
        self.assertEqual(set(story["catalog"]),{"A1","V1","V2"})
        self.assertEqual(story["source_sha256"],self.hash)
        self.add_stage("N04",{
            "story_timeline.json":story,
            "event_claims.jsonl":[json.loads(x) for x in (ctx4.out/"event_claims.jsonl").read_text().splitlines()],
            "unresolved.jsonl":[json.loads(x) for x in (ctx4.out/"unresolved.jsonl").read_text().splitlines()]})
        self.update_state()
        ctx5=self.ctx("N05")
        _n05(ctx5)
        txt=(ctx5.out/"review_final.txt").read_text(encoding="utf8")
        self.assertIn("A yellow star.",txt)
        self.assertNotIn("Trong cảnh thử nghiệm có một hình vuông đỏ",txt)
        rows=[json.loads(x) for x in (ctx5.out/"sentence_claims.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows),1)  # QA worker downstream still supports one sentence
        self.assertTrue(rows[0]["qa_truncated"])
        self.assertTrue(rows[0]["human_review_required"])
        ledgers=[json.loads(x) for x in (ctx5.out/"evidence_ledger.jsonl").read_text().splitlines()]
        self.assertEqual(ledgers[0]["evidence_ids"],["V1"])
        self.assertEqual(ledgers[0]["source_sha256"],self.hash)

if __name__=="__main__":
    unittest.main()
