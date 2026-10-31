"""No injected host process may run without a device-scoped G0 grant."""
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from review_phim_runtime.g0_security import G0ReadGrant, run_bound_g0

NOW = datetime(2026, 10, 31, 4, 0, tzinfo=timezone.utc)

@dataclass
class FakeDeviceRunner:
    device_id: str = 'device-A'
    def __post_init__(self):
        self.invocations = 0
    def __call__(self, argv):
        self.invocations += 1
        return {'returncode': 0, 'stdout': 'metadata', 'stderr': ''}

class GateTests(unittest.TestCase):
    def setUp(self):
        self.device = FakeDeviceRunner()
        self.grant = G0ReadGrant(device_id='device-A',scope_id='scope-101',
                                 operations=frozenset({'G0_INVENTORY'}),
                                 not_before=NOW-timedelta(minutes=1),
                                 expires_at=NOW+timedelta(minutes=2),
                                 authorization_ref='approval-101')
        self.collects = 0
    def collector(self, device_id, runner, *, approved):
        self.collects += 1
        self.assertTrue(approved)
        self.assertEqual(device_id, 'device-A')
        runner(['readonly-metadata-probe'])
        return 'G0_OBSERVED'
    def invoke(self, *, grant=None, device=None, verifier=None, now=NOW, operation='G0_INVENTORY'):
        return run_bound_g0('device-A', grant if grant is not None else self.grant,
                            device if device is not None else self.device,
                            verifier if verifier is not None else (lambda g,dev,op: True),
                            now=now, operation=operation, collector=self.collector)
    def test_success_calls_collector_only_after_verification(self):
        result = self.invoke()
        self.assertEqual(result.status, 'G0_OBSERVED')
        self.assertEqual(self.device.invocations, 1)
    def test_wrong_device_and_expired_grant_never_execute(self):
        for grant in [G0ReadGrant('other', 'scope', frozenset({'G0_INVENTORY'}),NOW,NOW+timedelta(minutes=2),'x'),
                      G0ReadGrant('device-A', 'scope', frozenset({'G0_INVENTORY'}),NOW-timedelta(minutes=2),NOW,'x')]:
            with self.subTest(grant=grant):
                self.assertNotEqual(self.invoke(grant=grant).status, 'G0_OBSERVED')
        self.assertEqual(self.device.invocations,0)
    def test_untrusted_issuer_response_is_fail_closed(self):
        for verdict in [False, None, 'true', 1]:
            with self.subTest(verdict=verdict):
                self.assertEqual(self.invoke(verifier=lambda *_: verdict).status, 'BLOCKED_G0_VERIFICATION')
        self.assertEqual(self.device.invocations,0)
    def test_mismatched_connector_device_never_executes(self):
        other = FakeDeviceRunner(device_id='device-B')
        self.assertEqual(self.invoke(device=other).status,'BLOCKED_G0_DEVICE')
        self.assertEqual(other.invocations,0)
    def test_unapproved_operation_never_executes(self):
        self.assertEqual(self.invoke(operation='PROCESS_MEDIA').status,'BLOCKED_G0_OPERATION')
        self.assertEqual(self.device.invocations,0)
    def test_missing_or_invalid_grant_never_executes(self):
        invalid=G0ReadGrant(device_id='device-A',scope_id='',operations=frozenset({'G0_INVENTORY'}),not_before=NOW,expires_at=NOW+timedelta(minutes=1),authorization_ref='')
        self.assertEqual(self.invoke(grant=invalid).status,'BLOCKED_G0_GRANT')
        self.assertEqual(self.device.invocations,0)
    def test_future_grant_never_executes(self):
        self.assertEqual(self.invoke(now=NOW-timedelta(hours=2)).status,'BLOCKED_G0_EXPIRED')
    def test_verifier_exception_never_executes(self):
        def broken(*args): raise RuntimeError('auth service unavailable')
        self.assertEqual(self.invoke(verifier=broken).status,'BLOCKED_G0_VERIFICATION')
        self.assertEqual(self.device.invocations,0)

if __name__ == '__main__': unittest.main()
