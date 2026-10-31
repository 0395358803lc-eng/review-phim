"""Process identity must survive PID reuse and crashes (synthetic only)."""
import unittest
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import datetime, timezone
from review_phim_runtime.gpu_lease_store import DurableGpuLeaseStore, ProcessStatus

NOW=datetime(2026,10,31,8,0,tzinfo=timezone.utc)

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


class ProcessIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=str(Path(self.temp.name)/'leases.sqlite3')
        self.store=DurableGpuLeaseStore(self.path)
        self.assertEqual(self.store.claim(job_id='job',device_id='dev-A',gpu_mib=3000,
             cpu_workers=1,heavy_gpu=True,telemetry=Sample(),now=NOW).status,'RESERVED')

    def ended(self,pid=123,start=10000,state='EXITED',device='dev-A'):
        return lambda *_: ProcessStatus(device,pid,start,state)

    def test_pid_only_binding_does_not_authorize_release(self):
        self.assertFalse(self.store.bind_pid('dev-A','job',123))
        self.assertEqual(self.store.release('dev-A','job',process_ended=lambda *_: True).status,
                         'BLOCKED_UNRECONCILED')
        self.assertEqual(self.store.get('dev-A','job').status,'RESERVED')

    def test_started_identity_required_to_release(self):
        self.assertTrue(self.store.bind_process_identity('dev-A','job',123,10000))
        self.assertEqual(self.store.release('dev-A','job',process_ended=self.ended()).status,'RELEASED')

    def test_pid_reused_with_different_start_does_not_release(self):
        self.assertTrue(self.store.bind_process_identity('dev-A','job',123,10000))
        self.assertEqual(self.store.release('dev-A','job',process_ended=self.ended(start=99999)).status,
                         'BLOCKED_UNRECONCILED')
        self.assertEqual(self.store.get('dev-A','job').status,'RESERVED')

    def test_process_still_running_does_not_release(self):
        self.assertTrue(self.store.bind_process_identity('dev-A','job',123,10000))
        self.assertEqual(self.store.release('dev-A','job',process_ended=self.ended(state='RUNNING')).status,
                         'BLOCKED_UNRECONCILED')

    def test_wrong_device_or_pid_does_not_release(self):
        self.assertTrue(self.store.bind_process_identity('dev-A','job',123,10000))
        for checker in (self.ended(pid=987), self.ended(device='dev-B')):
            self.assertEqual(self.store.release('dev-A','job',process_ended=checker).status,
                             'BLOCKED_UNRECONCILED')

    def test_legacy_boolean_callback_cannot_release(self):
        self.assertTrue(self.store.bind_process_identity('dev-A','job',123,10000))
        self.assertEqual(self.store.release('dev-A','job',process_ended=lambda *_: True).status,
                         'BLOCKED_UNRECONCILED')

    def test_unknown_process_identity_fails_closed(self):
        for pid,start in [(0,100),(-1,100),(123,0),(123,-1),(True,100),(123,True)]:
            with self.subTest(pid=pid,start=start):
                self.assertFalse(self.store.bind_process_identity('dev-A','job',pid,start))
        self.assertEqual(self.store.get('dev-A','job').status,'RESERVED')

    def test_process_identity_survives_database_reopen(self):
        self.assertTrue(self.store.bind_process_identity('dev-A','job',123,10000))
        reopened=DurableGpuLeaseStore(self.path)
        self.assertEqual(reopened.get('dev-A','job').process_started_ns,10000)
        self.assertEqual(reopened.release('dev-A','job',process_ended=self.ended()).status,'RELEASED')

    def test_process_reporter_failure_blocks(self):
        self.assertTrue(self.store.bind_process_identity('dev-A','job',123,10000))
        def fail(*_): raise RuntimeError('connector offline')
        self.assertEqual(self.store.release('dev-A','job',process_ended=fail).status,
                         'BLOCKED_UNRECONCILED')


if __name__=='__main__':
    unittest.main()
