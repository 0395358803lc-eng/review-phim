"""External Agent Skills can call Stage4 as a safe CLI, without model installs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from stage4.cli import main

SHA=hashlib.sha256(b"synthetic-file").hexdigest()

class Stage4CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.vision=self.root/"vision.jsonl"
        self.vision.write_text(json.dumps({"id":"V1","start_s":0,"end_s":2,
           "description":"A blue circle.","source_sha256":SHA})+"\n")
        self.speech=self.root/"speech.jsonl"
        self.speech.write_text(json.dumps({"id":"A1","start_s":0.2,"end_s":1.6,
           "text":"Một hình tròn màu xanh.","source_sha256":SHA})+"\n")
        self.out=self.root/"drafts"
    def command(self):
        return ["draft","--visual",str(self.vision),
          "--asr",str(self.speech),"--source-sha256",SHA,
          "--source-duration","3","--output-dir",str(self.out)]
    def test_cli_creates_bounded_multi_sentence_draft_and_citations(self):
        self.assertEqual(main(self.command()),0)
        self.assertIn("A blue circle.",(self.out/"review_draft.txt").read_text(encoding="utf8"))
        ledger=[json.loads(x) for x in (self.out/"evidence_ledger.jsonl").read_text(encoding="utf8").splitlines()]
        self.assertEqual({x["evidence_ids"][0] for x in ledger},{"V1","A1"})
        self.assertTrue((self.out/"story_timeline.json").is_file())
    def test_cli_does_not_overwrite_existing_output(self):
        self.out.mkdir()
        (self.out/"review_draft.txt").write_text("PRESERVED")
        with self.assertRaises(FileExistsError):
            main(self.command())
        self.assertEqual((self.out/"review_draft.txt").read_text(),"PRESERVED")
if __name__=="__main__":
    unittest.main()
