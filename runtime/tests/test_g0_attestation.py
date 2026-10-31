"""TDD: device-bound G0 HMAC proof, test-only keys. No real host access."""
import dataclasses
from datetime import datetime, timedelta, timezone
import unittest

from review_phim_runtime.g0_security import G0ReadGrant
from review_phim_runtime.g0_attestation import G0GrantAuthority, SignedG0Grant, run_signed_g0

NOW = datetime(2026, 10, 31, 8, tzinfo=timezone.utc)
KEY = b'A' * 32


class FakeRunner:
    device_id = "dev-1"
    def __init__(self): self.calls=0
    def __call__(self, argv):
        self.calls += 1
        return {"returncode":0, "stdout":"{}", "stderr":""}


class G0AttestationTests(unittest.TestCase):
    def setUp(self):
        self.authority = G0GrantAuthority(KEY)
        self.grant = G0ReadGrant(
            device_id="dev-1",scope_id="scope-1",operations=frozenset(
                {"G0_INVENTORY","G0_TELEMETRY"}),
            not_before=NOW-timedelta(minutes=1), expires_at=NOW+timedelta(minutes=5),
            authorization_ref="trusted-approval-1")
        self.signed = self.authority.sign(self.grant)
        self.runner = FakeRunner()

    def test_approved_signed_scope_allows_only_requested_g0_operation(self):
        self.assertTrue(self.authority.verify(self.signed,"dev-1","G0_INVENTORY",NOW))
        self.assertTrue(self.authority.verify(self.signed,"dev-1","G0_TELEMETRY",NOW))
        self.assertFalse(self.authority.verify(self.signed,"dev-1","PROCESS_MEDIA",NOW))
        self.assertFalse(self.authority.verify(self.signed,"dev-2","G0_INVENTORY",NOW))

    def test_signature_tampering_expiry_operation_and_device_are_rejected(self):
        for changed in (
            dataclasses.replace(self.grant,device_id="dev-2"),
            dataclasses.replace(self.grant,scope_id="scope-X"),
            dataclasses.replace(self.grant,authorization_ref="approval-X"),
            dataclasses.replace(self.grant,expires_at=NOW+timedelta(hours=1)),
            dataclasses.replace(self.grant,operations=frozenset({"G0_INVENTORY","PROCESS_MEDIA"})),
        ):
            with self.subTest(changed=changed):
                self.assertFalse(self.authority.verify(
                    dataclasses.replace(self.signed,grant=changed),
                    changed.device_id, "G0_INVENTORY", NOW))

    def test_signature_not_reusable_with_another_signing_key(self):
        self.assertFalse(G0GrantAuthority(b'B'*32).verify(self.signed,"dev-1","G0_INVENTORY",NOW))

    def test_invalid_mac_is_rejected(self):
        bad=dataclasses.replace(self.signed,mac="0"*64)
        self.assertFalse(self.authority.verify(bad,"dev-1","G0_INVENTORY",NOW))
        self.assertFalse(self.authority.verify(
            dataclasses.replace(self.signed,mac="not-a-digest"),
            "dev-1","G0_INVENTORY",NOW))

    def test_expired_future_and_naive_time_fail_closed(self):
        for t in (NOW+timedelta(minutes=5),NOW-timedelta(minutes=2),datetime(2026,10,31,8)):
            with self.subTest(time=t):
                self.assertFalse(self.authority.verify(self.signed,"dev-1","G0_INVENTORY",t))

    def test_invalid_grants_cannot_be_signed(self):
        for grant in (
            dataclasses.replace(self.grant,operations=frozenset({"G0_INVENTORY","PROCESS_MEDIA"})),
            dataclasses.replace(self.grant,operations=frozenset()),
            dataclasses.replace(self.grant,expires_at=NOW+timedelta(days=1)),
            dataclasses.replace(self.grant,scope_id=""),
            dataclasses.replace(self.grant,not_before=datetime(2026,10,31,8)),
        ):
            with self.subTest(grant=grant),self.assertRaises(ValueError):
                self.authority.sign(grant)

    def test_weak_or_empty_secret_rejected(self):
        for key in (b'', b'1234', 'not bytes', None):
            with self.subTest(key=key),self.assertRaises(ValueError):
                G0GrantAuthority(key)

    def test_bound_collector_does_not_run_with_unsigned_or_wrong_device(self):
        calls=[]
        def collector(device_id,runner,*,approved):
            calls.append((device_id,approved))
            runner(("safe",))
            return "G0_OBSERVED"
        bad=dataclasses.replace(self.signed,mac="0"*64)
        self.assertEqual(run_signed_g0(
            "dev-1",bad,self.runner,self.authority,now=NOW,
            collector=collector).status,"BLOCKED_G0_VERIFICATION")
        self.assertEqual(run_signed_g0(
            "dev-2",self.signed,self.runner,self.authority,now=NOW,
            collector=collector).status,"BLOCKED_G0_DEVICE")
        self.assertEqual(self.runner.calls,0)
        self.assertEqual(calls,[])

    def test_bound_collector_allows_valid_scope_after_verification(self):
        def collector(device_id,runner,*,approved):
            self.assertTrue(approved)
            runner(("metadata",))
            return "G0_OBSERVED"
        r=run_signed_g0(
            "dev-1",self.signed,self.runner,self.authority,now=NOW,collector=collector)
        self.assertEqual(r.status,"G0_OBSERVED")
        self.assertEqual(self.runner.calls,1)


if __name__=="__main__":
    unittest.main()
