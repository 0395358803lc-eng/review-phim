"""Restrict Windows G0 connector traffic to fixed, read-only command vectors.

Transport must be a *trusted authenticated connector* that returns an
independently verified command-digest/device receipt. This class is a
structural guard, not a credential issuer and not a Windows process launcher.
No user-provided paths or arguments are allowed.
"""
from __future__ import annotations
import hashlib
from collections.abc import Callable, Mapping
from .g0_collector import G0_POWERSHELL_ARGV, G0_NVIDIA_ARGV
from .telemetry import TELEMETRY_CPU_ARGV, TELEMETRY_GPU_ARGV

_ALLOWED = frozenset((
    tuple(G0_POWERSHELL_ARGV),
    tuple(G0_NVIDIA_ARGV),
    tuple(TELEMETRY_CPU_ARGV),
    tuple(TELEMETRY_GPU_ARGV),
))
_MAX_STDOUT_BYTES = 65536
_MAX_STDERR_BYTES = 4096


class FixedG0WindowsAdapter:
    """Callable for fixed G0 probes; validates every connector receipt."""

    def __init__(self, device_id: str, transport: Callable):
        if not isinstance(device_id, str) or not device_id.strip() or not callable(transport):
            raise ValueError('A bound device and trusted transport are required')
        self.device_id = device_id
        self._transport = transport

    def __call__(self, argv: tuple[str, ...] | list[str]) -> dict[str, object]:
        if (type(argv) not in (tuple, list) or not argv
                or any(type(x) is not str for x in argv)):
            raise ValueError('Not an argument vector')
        vector = tuple(argv)
        if vector not in _ALLOWED:
            raise ValueError('Command not in fixed G0 allowlist')
        expected_sha = hashlib.sha256('\0'.join(vector).encode('utf-8')).hexdigest()
        try:
            raw = self._transport(self.device_id, vector)
        except Exception as exc:
            raise RuntimeError('Connector unavailable') from exc
        if not isinstance(raw, Mapping) or raw.get('device_id') != self.device_id:
            raise RuntimeError('Unbound response from connector')
        if raw.get('argv_sha256') != expected_sha:
            raise RuntimeError('Command receipt mismatch')
        stdout, stderr, code = raw.get('stdout'), raw.get('stderr'), raw.get('returncode')
        if (type(code) is not int or type(stdout) is not str or type(stderr) is not str
                or len(stdout.encode('utf-8')) > _MAX_STDOUT_BYTES
                or len(stderr.encode('utf-8')) > _MAX_STDERR_BYTES):
            raise RuntimeError('Invalid or oversized G0 response')
        return {'returncode': code, 'stdout': stdout, 'stderr': stderr}
