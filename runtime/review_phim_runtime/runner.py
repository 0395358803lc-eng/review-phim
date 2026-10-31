"""Safe runner boundary; execution requires an injected, approved host launcher."""
from dataclasses import dataclass
from typing import Callable, Mapping
from .contracts import WorkItem
from .scope import ApprovalScope, validate_scope


@dataclass(frozen=True)
class AdapterResult:
    status: str
    stdout: str = ''
    stderr: str = ''


class SafeRunner:
    def __init__(self, executable_allowlist: Mapping[str, str], launcher: Callable):
        self._executables = dict(executable_allowlist)
        self._launcher = launcher
        self._inflight: set[str] = set()

    def run(self, tool: str, item: WorkItem, args: list[str], grant: ApprovalScope,
            *, now, resolver=None) -> AdapterResult:
        gate = validate_scope(item, grant, now=now, resolver=resolver)
        if not gate.allowed:
            return AdapterResult(gate.reason)
        if tool not in self._executables:
            return AdapterResult('BLOCKED_EXECUTABLE')
        if item.idempotency_key in self._inflight:
            return AdapterResult('BLOCKED_INDETERMINATE')
        self._inflight.add(item.idempotency_key)
        try:
            completed = self._launcher([self._executables[tool], *args], shell=False)
        except (TimeoutError, OSError) as exc:
            return AdapterResult('BLOCKED_INDETERMINATE', stderr=type(exc).__name__)
        if completed['returncode']:
            return AdapterResult('FAIL', stderr=completed.get('stderr','')[:4096])
        # The idempotency record intentionally persists until a controlled reconcile.
        return AdapterResult('TECHNICAL_PASS', stdout=completed.get('stdout','')[:4096])
