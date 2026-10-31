"""TDD for signed host process-exit receipts, with synthetic process data."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from review_phim_runtime.gpu_lease_store import DurableGpuLeaseStore
from review_phim_runtime.process_attestation import (
    ProcessReceiptAuthority, HostProcessReceipt, release_with_attestation,
)

NOW=datetime(2026,10,31,10,tzinfo=timezone.utc)
KEY=b"Z"*32


@dataclass(frozen=True)
class Sample:
    device_id: str="dev1"
    observed_at: datetime=NOW
    gpu_name: str="RTX 4060"
    vram_total_mib: int=8188
    vram_free_mib: int=7332
    logical_processors: int=28
    cpu_utilization_pct: float=15
    gpu_utilization_pct: float=8


class SignedProcessReceiptTests(unittest.TestCase):
    def setUp(self):
        self.authority=ProcessReceiptAuthority(KEY)
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=DurableGpuLeaseStore(str(Path(self.temp.name)/"gpu.sqlite3"))
        self.store.claim(job_id="job-A",device_id="dev1",gpu_mib=1500,cpu_workers=1,
                         heavy_gpu=True,telemetry=Sample(),now=NOW)
        self.assertTrue(self.store.bind_process_identity("dev1","job-A",4321,10000000))
        self.receipt=self.authority.sign(
            "dev1","job-A",4321,10000000,"EXITED",NOW)

    def release(self,receipt=None,authority=None,now=NOW,job="job-A"):
        return release_with_attestation(self.store,"dev1",job,
            receipt if receipt is not None else self.receipt,
            authority if authority is not None else self.authority,now=now)

    def test_valid_exit_receipt_releases_only_matching_lease(self):
        result=self.release()
        self.assertEqual(result.status,"RELEASED")
        self.assertEqual(self.store.get("dev1","job-A").status,"RELEASED")

    def test_tampering_state_pid_start_or_job_blocks(self):
        for field,value in (("state","RUNNING"),("pid",4322),
                            ("process_started_ns",10000001),("job_id","job-B"),
                            ("device_id","other")):
            with self.subTest(field=field):
                modified=replace(self.receipt,**{field:value})
                self.assertEqual(self.release(receipt=modified).status,"BLOCKED_UNRECONCILED")
        self.assertEqual(self.store.get("dev1","job-A").status,"RESERVED")

    def test_fake_signature_or_wrong_signing_key_blocks(self):
        tampered=replace(self.receipt,mac="0"*64)
        self.assertEqual(self.release(receipt=tampered).status,"BLOCKED_UNRECONCILED")
        self.assertEqual(self.release(authority=ProcessReceiptAuthority(b"Y"*32)).status,
                         "BLOCKED_UNRECONCILED")

    def test_stale_future_or_naive_clock_blocks(self):
        for t in (NOW+timedelta(seconds=30),NOW-timedelta(seconds=2),
                  datetime(2026,10,31,10)):
            with self.subTest(time=t):
                self.assertEqual(self.release(now=t).status,"BLOCKED_UNRECONCILED")

    def test_receipt_for_another_job_cannot_reclaim_other_job(self):
        self.assertEqual(self.release(job="job-B").status,"BLOCKED_UNRECONCILED")
        self.assertEqual(self.store.get("dev1","job-A").status,"RESERVED")

    def test_unsigned_legacy_process_status_cannot_release(self):
        from review_phim_runtime.gpu_lease_store import ProcessStatus
        legacy=ProcessStatus("dev1",4321,10000000,"EXITED")
        self.assertEqual(self.release(receipt=legacy).status,"BLOCKED_UNRECONCILED")

    def test_can_only_sign_known_process_states(self):
        with self.assertRaises(ValueError):
            self.authority.sign("dev1","job-A",4321,10000000,"SUCCESS",NOW)

    def test_invalid_pid_start_or_secret_rejected(self):
        with self.assertRaises(ValueError):
            ProcessReceiptAuthority(b"weak")
        for pid,start in ((-1,10),(4321,0),(True,100)):
            with self.subTest(pid=pid,start=start),self.assertRaises(ValueError):
                self.authority.sign("dev1","job-A",pid,start,"EXITED",NOW)


if __name__=="__main__":
    unittest.main()
