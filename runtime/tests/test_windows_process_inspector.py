"""Windows CI: inspect only a synthetic child process, not media or the user's host."""
import os
import sys
import subprocess
import unittest
from review_phim_runtime.gpu_lease_store import ProcessStatus
from review_phim_runtime.windows_process_inspector import (
    read_windows_process_identity, observe_windows_process,
)


class WindowsProcessInspectorTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt','Windows-only Windows process API')
    def test_observes_synthetic_child_and_checks_process_creation(self):
        process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'])
        try:
            identity=read_windows_process_identity(process.pid)
            self.assertIsNotNone(identity)
            self.assertGreater(identity.start_time_ns,0)
            self.assertEqual(identity.pid,process.pid)
            expected=ProcessStatus('ci-device',process.pid,identity.start_time_ns,'UNKNOWN')
            self.assertEqual(observe_windows_process('ci-device',expected).state,'RUNNING')
            different=ProcessStatus('ci-device',process.pid,identity.start_time_ns+100,'UNKNOWN')
            self.assertEqual(observe_windows_process('ci-device',different).state,'UNKNOWN')
            self.assertEqual(observe_windows_process('foreign-device',expected).state,'UNKNOWN')
            process.terminate()
            process.wait(timeout=5)
            self.assertEqual(observe_windows_process('ci-device',expected).state,'EXITED')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)

    def test_missing_or_invalid_identity_fails_closed(self):
        for pid,start in ((0,100),(-1,100),(100,0),(True,100)):
            with self.subTest(pid=pid,start=start):
                identity=ProcessStatus('ci',pid,start,'UNKNOWN')
                self.assertEqual(observe_windows_process('ci',identity).state,'UNKNOWN')


if __name__=='__main__': unittest.main()
