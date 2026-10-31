"""Tamper-evident G0 scope *contract* using host-held HMAC-SHA256 keys.

Never store issuer keys in the repository, a generated evidence packet, a
model prompt, or a user-visible connector response. The signing authority
is meaningful only inside an authenticated host/connector trusted boundary.
No real host issuer or device connection is implemented in this module.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json

from .g0_security import G0ReadGrant, G0GuardResult, run_bound_g0


_G0_OPERATIONS = frozenset({"G0_INVENTORY", "G0_TELEMETRY"})
_MAX_GRANT_SECONDS = 900


@dataclass(frozen=True)
class SignedG0Grant:
    grant: G0ReadGrant
    mac: str


def _valid_grant(grant: object) -> bool:
    if not isinstance(grant, G0ReadGrant):
        return False
    if not all(type(v) is str and bool(v.strip()) for v in (
            grant.device_id, grant.scope_id, grant.authorization_ref)):
        return False
    if (type(grant.operations) is not frozenset or not grant.operations
            or not grant.operations <= _G0_OPERATIONS):
        return False
    if not isinstance(grant.not_before, datetime) or not isinstance(grant.expires_at, datetime):
        return False
    if (grant.not_before.tzinfo is None or grant.expires_at.tzinfo is None
            or grant.not_before.utcoffset() is None or grant.expires_at.utcoffset() is None):
        return False
    duration = (grant.expires_at - grant.not_before).total_seconds()
    return 0 < duration <= _MAX_GRANT_SECONDS


def _canonical_bytes(grant: G0ReadGrant) -> bytes:
    data = {
        "domain": "review-phim/g0-read/v1",
        "device_id": grant.device_id,
        "scope_id": grant.scope_id,
        "operations": sorted(grant.operations),
        "not_before": grant.not_before.astimezone(timezone.utc).isoformat(timespec="microseconds"),
        "expires_at": grant.expires_at.astimezone(timezone.utc).isoformat(timespec="microseconds"),
        "authorization_ref": grant.authorization_ref,
    }
    return json.dumps(data, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


class G0GrantAuthority:
    """Keyed signer/verifier for trusted host-side G0 grants (no key storage)."""

    def __init__(self, key: bytes):
        if type(key) is not bytes or len(key) < 32:
            raise ValueError("A host-managed key of at least 32 bytes is required")
        self._key = key

    def sign(self, grant: G0ReadGrant) -> SignedG0Grant:
        if not _valid_grant(grant):
            raise ValueError("Invalid or overbroad G0 grant")
        digest = hmac.new(self._key, _canonical_bytes(grant), hashlib.sha256).hexdigest()
        return SignedG0Grant(grant, digest)

    def verify(self, signed: SignedG0Grant, device_id: str,
               operation: str, now: datetime) -> bool:
        if not isinstance(signed, SignedG0Grant) or not _valid_grant(signed.grant):
            return False
        grant = signed.grant
        if (type(device_id) is not str or grant.device_id != device_id
                or type(operation) is not str or operation not in grant.operations):
            return False
        if (not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None or not grant.not_before <= now < grant.expires_at):
            return False
        if (type(signed.mac) is not str or len(signed.mac) != 64
                or any(c not in "0123456789abcdef" for c in signed.mac)):
            return False
        expected = hmac.new(self._key, _canonical_bytes(grant), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signed.mac)


def run_signed_g0(device_id: str, signed: SignedG0Grant, device_runner,
                  authority: G0GrantAuthority, *, now: datetime,
                  collector=None) -> G0GuardResult:
    """Integrate the HMAC verification contract with the existing G0 gate.

    Device runner, authoritative clock and key provider must be from a
    trusted authenticated host connector. This function does not supply them.
    """
    if not isinstance(signed, SignedG0Grant) or not isinstance(authority, G0GrantAuthority):
        return G0GuardResult("BLOCKED_G0_VERIFICATION")
    def verify(grant, requested_device, operation):
        return (grant == signed.grant and
                authority.verify(signed, requested_device, operation, now))
    return run_bound_g0(
        device_id, signed.grant, device_runner, verify,
        now=now, operation="G0_INVENTORY", collector=collector,
    )
