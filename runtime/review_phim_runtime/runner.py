"""Safe runner boundary; execution requires an injected, approved host launcher."""
from dataclasses import dataclass
from typing import Callable, Mapping
from .contracts import WorkItem
from .scope import ApprovalScope, validate_scope
from .journal import OperationJournal


@dataclass(frozen=True)
class AdapterResult:
    status: str
    stdout: str = ''
    stderr: str = ''


class SafeRunner:
    def __init__(self, executable_allowlist: Mapping[str, str], launcher: Callable,
                 arg_validator: Callable[[str, WorkItem, list[str]], bool] | None = None,
                 journal: OperationJournal | None = None):
        self._executables = dict(executable_allowlist)
        self._launcher = launcher
        self._arg_validator = arg_validator
        self._journal = journal
        self._inflight: set[str] = set()

    def run(self, tool: str, item: WorkItem, args: list[str], grant: ApprovalScope,
            *, now, resolver=None) -> AdapterResult:
        gate = validate_scope(item, grant, now=now, resolver=resolver)
        if not gate.allowed:
            return AdapterResult(gate.reason)
        if tool not in self._executables:
            return AdapterResult('BLOCKED_EXECUTABLE')
        if (self._arg_validator is None or not self._arg_validator(tool,item,args)):
            return AdapterResult('BLOCKED_ARGUMENTS')
        if self._journal is None:
            return AdapterResult('BLOCKED_JOURNAL_UNAVAILABLE')
        if not grant.scope_id:
            return AdapterResult('BLOCKED_SCOPE_ID')
        if item.idempotency_key in self._inflight:
            return AdapterResult('BLOCKED_INDETERMINATE')
        try:
            reservation = self._journal.reserve(grant.scope_id, item.idempotency_key, item.estimated_bytes, grant.max_bytes)
        except Exception:
            return AdapterResult('BLOCKED_JOURNAL_UNAVAILABLE')
        if reservation.status != 'RESERVED':
            return AdapterResult(reservation.status)
        self._inflight.add(item.idempotency_key)
        try:
            completed = self._launcher([self._executables[tool], *args], shell=False)
        except (TimeoutError, OSError) as exc:
            return AdapterResult('BLOCKED_INDETERMINATE', stderr=type(exc).__name__)
        # A completed launch must identify the OS process; otherwise treat result as uncertain.
        pid, rc = completed.get('pid'), completed.get('returncode')
        try:
            if not self._journal.mark_running(grant.scope_id, item.idempotency_key, pid):
                return AdapterResult('BLOCKED_INDETERMINATE')
            if not self._journal.mark_completed(grant.scope_id, item.idempotency_key, rc):
                return AdapterResult('BLOCKED_INDETERMINATE')
        except Exception:
            return AdapterResult('BLOCKED_INDETERMINATE')
        if rc:
            return AdapterResult('FAIL', stderr=completed.get('stderr','')[:4096])
        # The idempotency record intentionally persists until a controlled reconcile.
        return AdapterResult('TECHNICAL_PASS', stdout=completed.get('stdout','')[:4096])
