"""QA host must lock the transitively imported Stage4 source modules."""
import hashlib
from pathlib import Path
import unittest
from qa.acceptance_engine_real_models import pinned_code_inputs

ROOT=Path(__file__).resolve().parents[1]

class RuntimePins(unittest.TestCase):
    def test_every_stage4_module_and_worker_is_SHA_pinned(self):
        worker=ROOT/"qa"/"legacy_offline_worker.py"
        paths=pinned_code_inputs(ROOT,worker)
        expected=[worker,*sorted((ROOT/"stage4").glob("*.py")),
            *sorted((ROOT/"stage5").glob("*.py")),
            ROOT/"skills"/"film-review-orchestrator"/"scripts"/"evidence_qc.py"]
        self.assertEqual(set(paths),{str(p.resolve(strict=True)) for p in expected})
        for p in expected:
            self.assertEqual(paths[str(p.resolve())],hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=="__main__":
    unittest.main()
