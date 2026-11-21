"""Every Stage5 helper and Qwen weight must be pinned by trusted host config."""
import hashlib
from pathlib import Path
import unittest
from qa.acceptance_engine_real_models import pinned_code_inputs,extra_model_sha_files
ROOT=Path(__file__).resolve().parents[1]
class PinningTests(unittest.TestCase):
    def test_stage5_modules_also_in_sha_pins(self):
        pins=pinned_code_inputs(ROOT,ROOT/"qa"/"legacy_offline_worker.py")
        for path in (ROOT/"stage5").glob("*.py"):
            self.assertEqual(pins[str(path.resolve(strict=True))],
                hashlib.sha256(path.read_bytes()).hexdigest())
    def test_n07_pins_both_real_model_weight_files(self):
        extras=extra_model_sha_files("N07")
        self.assertEqual(set(extras),{
            "embeddings/clip-vit-base-patch32/pytorch_model.bin",
            "vision/qwen3-vl-2b-instruct/model.safetensors"})
if __name__=="__main__":unittest.main()
