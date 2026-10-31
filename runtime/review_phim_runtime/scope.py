"""Fail-closed operation scoping. A verified host path resolver is mandatory."""
from dataclasses import dataclass
from datetime import datetime
import ntpath
from typing import Callable
from .contracts import WorkItem, SourceInterval


@dataclass(frozen=True)
class ApprovalScope:
    device_id: str
    job_id: str
    allowed_root: str
    allowed_operations: frozenset[str]
    interval: SourceInterval
    max_bytes: int
    expires_at: datetime
    scope_id: str = ''


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str


def _windows_under(path: str, root: str) -> bool:
    path, root = ntpath.normcase(ntpath.normpath(path)), ntpath.normcase(ntpath.normpath(root))
    try:
        path_drive, root_drive = ntpath.splitdrive(path)[0], ntpath.splitdrive(root)[0]
        if not (len(path_drive) == 2 and len(root_drive) == 2 and path_drive[1] == root_drive[1] == ":" and path_drive[0].isalpha() and root_drive[0].isalpha()):
            return False
        return ntpath.isabs(path) and ntpath.isabs(root) and ntpath.commonpath([path, root]) == root
    except ValueError:
        return False


def validate_scope(request: WorkItem, grant: ApprovalScope, *, now: datetime,
                   resolver: Callable[[str], str] | None = None) -> ScopeDecision:
    def blocked(reason: str) -> ScopeDecision:
        return ScopeDecision(False, reason)
    if request.device_id != grant.device_id or request.job_id != grant.job_id:
        return blocked('BLOCKED_DEVICE_OR_JOB')
    if now >= grant.expires_at:
        return blocked('BLOCKED_EXPIRED')
    if request.operation not in grant.allowed_operations:
        return blocked('BLOCKED_OPERATION')
    if request.estimated_bytes < 0 or request.estimated_bytes > grant.max_bytes:
        return blocked('BLOCKED_QUOTA')
    if request.interval.start_s < grant.interval.start_s or request.interval.end_s > grant.interval.end_s:
        return blocked('BLOCKED_INTERVAL')
    if resolver is None:
        return blocked('BLOCKED_CANONICAL_UNAVAILABLE')
    # Never allow lexical traversal even when canonicalization normalizes it back inside.
    if '..' in request.path.replace('/', '\\').split('\\'):
        return blocked('BLOCKED_SOURCE_OR_SCOPE')
    try:
        path, root = resolver(request.path), resolver(grant.allowed_root)
    except (OSError, ValueError, RuntimeError):
        return blocked('BLOCKED_CANONICAL_UNAVAILABLE')
    if not _windows_under(path, root):
        return blocked('BLOCKED_SOURCE_OR_SCOPE')
    return ScopeDecision(True, 'ALLOW')
