"""G0 read authorization boundary requiring connector-issued verification.

Verifier and device runner must originate from a trusted connector, not the
requester. This module issues no authority by itself and never touches media.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(frozen=True)
class G0ReadGrant:
    device_id: str
    scope_id: str
    operations: frozenset[str]
    not_before: datetime
    expires_at: datetime
    authorization_ref: str


@dataclass(frozen=True)
class G0GuardResult:
    status: str
    observation: object | None = None


def validate_g0_read_scope(device_id: str, grant: G0ReadGrant, device_runner,
                           verifier: Callable, *, now: datetime, operation: str) -> str:
    """Return ALLOW only for an issuer-attested, device-bound G0 read scope."""
    if not isinstance(device_id, str) or not device_id.strip() or not isinstance(grant, G0ReadGrant):
        return 'BLOCKED_G0_GRANT'
    if (not grant.scope_id or not grant.authorization_ref or not grant.device_id
            or type(grant.operations) is not frozenset
            or not isinstance(grant.not_before, datetime)
            or not isinstance(grant.expires_at, datetime)
            or not isinstance(now, datetime)
            or not all(x.tzinfo is not None and x.utcoffset() is not None
                       for x in (grant.not_before, grant.expires_at, now))):
        return 'BLOCKED_G0_GRANT'
    if grant.device_id != device_id or getattr(device_runner, 'device_id', None) != device_id:
        return 'BLOCKED_G0_DEVICE'
    if operation not in frozenset({'G0_INVENTORY','G0_TELEMETRY'}) or operation not in grant.operations:
        return 'BLOCKED_G0_OPERATION'
    if not grant.not_before <= now < grant.expires_at:
        return 'BLOCKED_G0_EXPIRED'
    try:
        if verifier(grant, device_id, operation) is not True:
            return 'BLOCKED_G0_VERIFICATION'
    except Exception:
        return 'BLOCKED_G0_VERIFICATION'
    return 'ALLOW'


def run_bound_g0(device_id: str, grant: G0ReadGrant, device_runner,
                 verifier: Callable, *, now: datetime, operation: str = 'G0_INVENTORY',
                 collector=None) -> G0GuardResult:
    """Run fixed G0 collection only after connector verifier passes."""
    if operation != 'G0_INVENTORY':
        return G0GuardResult('BLOCKED_G0_OPERATION')
    status = validate_g0_read_scope(device_id,grant,device_runner,verifier,now=now,operation=operation)
    if status != 'ALLOW':
        return G0GuardResult(status)
    if collector is None:
        from .g0_collector import collect_g0
        collector = collect_g0
    try:
        observation = collector(device_id, device_runner, approved=True)
    except Exception:
        return G0GuardResult('BLOCKED_G0_COLLECTOR')
    return G0GuardResult(getattr(observation, 'status', observation if isinstance(observation, str)
                              else 'BLOCKED_G0_COLLECTOR'), observation)
