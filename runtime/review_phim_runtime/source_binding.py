"""Source SHA-256 verification using one connector-approved open handle.

This code is NOT permission to read media: authorization, canonical file
identity, and a handle tied to the verified path MUST be supplied by a
trusted Windows host adapter. No film access, process or network occurs here.
"""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import ntpath
from typing import BinaryIO, Callable

from .winpaths import _validate_local_drive_path


@dataclass(frozen=True)
class SourceReadGrant:
    device_id: str
    job_id: str
    path: str
    source_sha256: str
    source_bytes: int
    operation: str
    process_approval_ref: str
    not_before: datetime
    expires_at: datetime


@dataclass(frozen=True)
class OpenSource:
    canonical_path: str
    file_identity: str
    stream: BinaryIO


@dataclass(frozen=True)
class SourceVerification:
    status: str
    actual_sha256: str | None = None
    actual_bytes: int | None = None
    file_identity: str | None = None


def _valid_scope(grant: object, now: datetime) -> bool:
    if not isinstance(grant, SourceReadGrant):
        return False
    if not all(type(x) is str and x.strip() for x in (
            grant.device_id, grant.job_id, grant.path, grant.process_approval_ref)):
        return False
    if grant.operation != 'SOURCE_HASH' or (
            type(grant.source_sha256) is not str
            or len(grant.source_sha256) != 64
            or any(c not in '0123456789abcdef' for c in grant.source_sha256)):
        return False
    if type(grant.source_bytes) is not int or grant.source_bytes <= 0:
        return False
    if any(not isinstance(x, datetime) or x.tzinfo is None or x.utcoffset() is None
           for x in (grant.not_before, grant.expires_at, now)):
        return False
    if not grant.not_before <= now < grant.expires_at:
        return False
    try:
        _validate_local_drive_path(grant.path)
    except ValueError:
        return False
    return True


def verify_bound_source(grant: SourceReadGrant, reader,
                        verifier: Callable, *, now: datetime,
                        chunk_bytes: int = 1024 * 1024) -> SourceVerification:
    """Observe approved SHA-256 from one opened handle, returning metadata only.

    The caller must NOT expose the verifier or reader to untrusted code. In
    production, the verifier checks an issued PROCESS_APPROVED grant; the
    reader supplies an OS-verified, handle-bound canonical path and file ID.
    A future host adapter must also protect the source against concurrent
    mutation during hashing (file locks/consistency validation).
    """
    if not _valid_scope(grant, now):
        return SourceVerification('BLOCKED_SOURCE_SCOPE')
    if (getattr(reader, 'device_id', None) != grant.device_id or
            not callable(getattr(reader, 'open_verified', None))):
        return SourceVerification('BLOCKED_SOURCE_DEVICE')
    try:
        if verifier(grant,grant.device_id,'SOURCE_HASH') is not True:
            return SourceVerification('BLOCKED_SOURCE_APPROVAL')
    except Exception:
        return SourceVerification('BLOCKED_SOURCE_APPROVAL')
    if type(chunk_bytes) is not int or not 1 <= chunk_bytes <= 8 * 1024 * 1024:
        return SourceVerification('BLOCKED_SOURCE_SCOPE')
    try:
        with reader.open_verified(grant.path) as opened:
            if not isinstance(opened, OpenSource):
                return SourceVerification('BLOCKED_SOURCE_IDENTITY')
            _validate_local_drive_path(opened.canonical_path)
            if (ntpath.normcase(ntpath.normpath(opened.canonical_path)) !=
                    ntpath.normcase(ntpath.normpath(grant.path)) or
                    type(opened.file_identity) is not str or not opened.file_identity.strip()):
                return SourceVerification('BLOCKED_SOURCE_IDENTITY')
            digest = hashlib.sha256()
            total = 0
            while True:
                chunk = opened.stream.read(chunk_bytes)
                if type(chunk) is not bytes:
                    return SourceVerification('BLOCKED_SOURCE_READ')
                if not chunk:
                    break
                total += len(chunk)
                if total > grant.source_bytes:
                    return SourceVerification('BLOCKED_SOURCE_MISMATCH')
                digest.update(chunk)
            observed_hash = digest.hexdigest()
            if total != grant.source_bytes or not hmac.compare_digest(observed_hash,grant.source_sha256):
                return SourceVerification('BLOCKED_SOURCE_MISMATCH')
            return SourceVerification('SOURCE_HASH_MATCH',observed_hash,total,opened.file_identity)
    except (OSError, TypeError, ValueError, RuntimeError, AttributeError):
        return SourceVerification('BLOCKED_SOURCE_READ')
