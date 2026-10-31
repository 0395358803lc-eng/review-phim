"""Host-issued HMAC process-status receipts, bound to GPU lease identity.

This module enforces tamper evidence and freshness only. A signed EXITED
claim is trustworthy *only if* the issuer is a trusted authenticated Windows
host inspector that confirmed termination using a kernel handle.
The signer/key must never be exposed to user inputs or model prompts.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json

from .gpu_lease_store import DurableGpuLeaseStore, GpuLease, ProcessStatus


@dataclass(frozen=True)
class HostProcessReceipt:
    device_id: str
    job_id: str
    pid: int
    process_started_ns: int
    state: str
    observed_at: datetime
    mac: str


def _valid_fields(device_id, job_id, pid, start, state, observed_at) -> bool:
    return (
        type(device_id) is str and bool(device_id.strip())
        and type(job_id) is str and bool(job_id.strip())
        and type(pid) is int and 0 < pid < 2**32
        and type(start) is int and 0 < start < 2**63
        and type(state) is str and state in ('RUNNING','EXITED')
        and isinstance(observed_at,datetime)
        and observed_at.tzinfo is not None and observed_at.utcoffset() is not None
    )


def _canonical(receipt: HostProcessReceipt) -> bytes:
    return json.dumps({
        'domain':'review-phim/host-process-observation/v1',
        'device_id':receipt.device_id,
        'job_id':receipt.job_id,
        'pid':receipt.pid,
        'process_started_ns':receipt.process_started_ns,
        'state':receipt.state,
        'observed_at':receipt.observed_at.astimezone(timezone.utc).isoformat(timespec='microseconds'),
    },sort_keys=True,separators=(',',':')).encode('utf-8')


class ProcessReceiptAuthority:
    def __init__(self,key:bytes):
        if type(key) is not bytes or len(key) < 32:
            raise ValueError('Host-owned process receipt key >=32 bytes required')
        self._key=key

    def sign(self,device_id:str,job_id:str,pid:int,process_started_ns:int,
             state:str,observed_at:datetime) -> HostProcessReceipt:
        if not _valid_fields(device_id,job_id,pid,process_started_ns,state,observed_at):
            raise ValueError('Invalid process identity or observation')
        unsigned=HostProcessReceipt(device_id,job_id,pid,process_started_ns,state,observed_at,'')
        mac=hmac.new(self._key,_canonical(unsigned),hashlib.sha256).hexdigest()
        return HostProcessReceipt(device_id,job_id,pid,process_started_ns,state,observed_at,mac)

    def verify(self,receipt:object,device_id:str,job_id:str,pid:int,
               process_started_ns:int,now:datetime) -> bool:
        if not isinstance(receipt,HostProcessReceipt):
            return False
        if not _valid_fields(receipt.device_id,receipt.job_id,receipt.pid,
                             receipt.process_started_ns,receipt.state,receipt.observed_at):
            return False
        if (receipt.device_id != device_id or receipt.job_id != job_id or
                receipt.pid != pid or receipt.process_started_ns != process_started_ns or
                receipt.state != 'EXITED'):
            return False
        if not isinstance(now,datetime) or now.tzinfo is None or now.utcoffset() is None:
            return False
        age=(now-receipt.observed_at).total_seconds()
        if not 0 <= age <= 10:
            return False
        if (type(receipt.mac) is not str or len(receipt.mac) != 64 or
                any(c not in '0123456789abcdef' for c in receipt.mac)):
            return False
        expected=hmac.new(self._key,_canonical(receipt),hashlib.sha256).hexdigest()
        return hmac.compare_digest(receipt.mac,expected)


def release_with_attestation(store: DurableGpuLeaseStore,device_id:str,job_id:str,
                             receipt:HostProcessReceipt,authority:ProcessReceiptAuthority,
                             *,now:datetime) -> GpuLease:
    """Release only after a fresh host-signed EXITED claim matches persistent lease."""
    blocked=GpuLease('BLOCKED_UNRECONCILED')
    if not isinstance(store,DurableGpuLeaseStore) or not isinstance(authority,ProcessReceiptAuthority):
        return blocked
    entry=store.get(device_id,job_id)
    if entry is None or type(entry.pid) is not int or type(entry.process_started_ns) is not int:
        return blocked
    if not authority.verify(receipt,device_id,job_id,entry.pid,entry.process_started_ns,now):
        return blocked
    identity=ProcessStatus(device_id,entry.pid,entry.process_started_ns,'EXITED')
    return store.release(device_id,job_id,process_ended=lambda *_:identity)
