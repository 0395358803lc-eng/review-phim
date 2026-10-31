"""Durable admission tests use synthetic telemetry; no GPU/media device touched."""
import unittest
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory
from pathlib import Path
from review_phim_runtime.gpu_lease_store import DurableGpuLeaseStore

NOW=datetime(2026,10,31,5,0,tzinfo=timezone.utc)
@dataclass(frozen=True)
class Sample:
    device_id: str='dev-A'
    observed_at: datetime=NOW
    gpu_name: str='RTX 4060'
    vram_total_mib: int=8188
    vram_free_mib: int=7332
    logical_processors: int=28
    cpu_utilization_pct: float=15
    gpu_utilization_pct: float=5

class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=str(Path(self.temp.name)/'leases.db')
        self.db=DurableGpuLeaseStore(self.path)
        self.sample=Sample()
    def claim(self,job='j1',gpu=3000,cpu=2,heavy=True,sample=None,db=None,device='dev-A',now=NOW):
        return (db or self.db).claim(job_id=job,device_id=device,gpu_mib=gpu,
               cpu_workers=cpu,heavy_gpu=heavy,telemetry=sample or self.sample,now=now)
    def test_two_processes_cannot_book_heavy_gpu_concurrently(self):
        self.assertEqual(self.claim().status,'RESERVED')
        reopened=DurableGpuLeaseStore(self.path)
        self.assertEqual(self.claim(job='j2',db=reopened).status,'BLOCKED_GPU_BUSY')
        self.assertEqual(reopened.get('dev-A','j1').gpu_mib,3000)
    def test_cumulative_vram_budget_across_light_jobs(self):
        self.assertEqual(self.claim(job='x',gpu=3500,heavy=False).status,'RESERVED')
        self.assertEqual(self.claim(job='y',gpu=3000,heavy=False).status,'BLOCKED_GPU_BUDGET')
    def test_expired_telemetry_and_wrong_device_fail_closed(self):
        self.assertEqual(self.claim(now=NOW+timedelta(seconds=15)).status,'BLOCKED_TELEMETRY')
        self.assertEqual(self.claim(device='dev-B').status,'BLOCKED_TELEMETRY')
        self.assertEqual(self.claim(sample=replace(self.sample,gpu_utilization_pct=float('nan'))).status,'BLOCKED_TELEMETRY')
    def test_cpu_pressure_limits_workers(self):
        pressured=replace(self.sample,cpu_utilization_pct=95)
        self.assertEqual(self.claim(gpu=0,cpu=4,heavy=False,sample=pressured).status,'BLOCKED_CPU_BUDGET')
    def test_unknown_pid_cannot_release(self):
        self.assertEqual(self.claim().status,'RESERVED')
        self.assertEqual(self.db.release('dev-A','j1',process_ended=lambda *_: True).status,'BLOCKED_UNRECONCILED')
        self.assertEqual(self.db.get('dev-A','j1').status,'RESERVED')
    def test_verified_process_completion_can_release(self):
        self.claim()
        self.assertTrue(self.db.bind_pid('dev-A','j1',2345))
        self.assertEqual(self.db.release('dev-A','j1',process_ended=lambda dev,pid: False).status,'BLOCKED_UNRECONCILED')
        self.assertEqual(self.db.release('dev-A','j1',process_ended=lambda dev,pid: (dev,pid)==('dev-A',2345)).status,'RELEASED')
        self.assertEqual(self.claim(job='j2').status,'RESERVED')
    def test_reservation_survives_restart_and_idempotency(self):
        self.claim()
        other=DurableGpuLeaseStore(self.path)
        self.assertEqual(self.claim(db=other).status,'BLOCKED_DUPLICATE')
        self.assertEqual(other.get('dev-A','j1').status,'RESERVED')
    def test_atomic_concurrent_admission_limits_total(self):
        def f(i):
            return DurableGpuLeaseStore(self.path).claim(job_id=f'j{i}',device_id='dev-A',gpu_mib=1300,
                  cpu_workers=1,heavy_gpu=False,telemetry=self.sample,now=NOW).status
        with ThreadPoolExecutor(max_workers=12) as pool: statuses=list(pool.map(f,range(12)))
        self.assertEqual(statuses.count('RESERVED'),4)
        self.assertEqual(statuses.count('BLOCKED_GPU_BUDGET'),8)
    def test_invalid_negative_gpu_and_cpu_rejected(self):
        self.assertEqual(self.claim(gpu=-1).status,'BLOCKED_RESOURCE_REQUEST')
        self.assertEqual(self.claim(cpu=-1).status,'BLOCKED_RESOURCE_REQUEST')

if __name__=='__main__':unittest.main()
