"""Read-only Windows process inspection with PID + real creation-time identity.

Never interpret a missing process as EXITED: only a still-queryable kernel
process object whose creation time matches the reserved identity can be
marked exited. This module performs no spawning, killing or file writes.
"""
from __future__ import annotations
import os

from .gpu_lease_store import ProcessStatus

_WINDOWS_TO_UNIX_EPOCH_100NS = 116444736000000000
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_SYNCHRONIZE = 0x00100000
_WAIT_OBJECT_0 = 0x00000000
_WAIT_TIMEOUT = 0x00000102


def _probe_windows_handle(pid: int) -> tuple[int, str] | None:
    """Read a single kernel process handle to eliminate PID lookup races."""
    if os.name != 'nt' or type(pid) is not int or not 0 < pid < 2**32:
        return None
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    )
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL

    handle = kernel.OpenProcess(
        _PROCESS_QUERY_LIMITED_INFORMATION | _SYNCHRONIZE, False, pid
    )
    if not handle:
        return None
    try:
        created, exited, kernel_time, user_time = (
            wintypes.FILETIME(), wintypes.FILETIME(),
            wintypes.FILETIME(), wintypes.FILETIME(),
        )
        if not kernel.GetProcessTimes(
            handle, ctypes.byref(created), ctypes.byref(exited),
            ctypes.byref(kernel_time), ctypes.byref(user_time)
        ):
            return None
        ticks = (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
        if ticks <= _WINDOWS_TO_UNIX_EPOCH_100NS:
            return None
        start_time_ns = (ticks - _WINDOWS_TO_UNIX_EPOCH_100NS) * 100
        if start_time_ns <= 0:
            return None
        wait_code = kernel.WaitForSingleObject(handle, 0)
        if wait_code == _WAIT_OBJECT_0:
            state = 'EXITED'
        elif wait_code == _WAIT_TIMEOUT:
            state = 'RUNNING'
        else:
            return None
        return start_time_ns, state
    finally:
        kernel.CloseHandle(handle)


def read_windows_process_identity(pid: int) -> ProcessStatus | None:
    """Read identity of an existing OS process; no credential or approval issued."""
    try:
        observed = _probe_windows_handle(pid)
    except (OSError, AttributeError, ValueError):
        return None
    if observed is None:
        return None
    return ProcessStatus('', pid, observed[0], observed[1])


def observe_windows_process(device_id: str, expected: ProcessStatus) -> ProcessStatus:
    """Compare PID and creation time; fail closed on missing or reused processes.

    Must be invoked exclusively through a trusted host connector bound to
    device_id. The device_id alone does not authenticate the calling host.
    """
    if not isinstance(expected, ProcessStatus):
        return ProcessStatus(device_id, 0, 0, 'UNKNOWN')
    unknown = ProcessStatus(device_id, expected.pid, expected.start_time_ns, 'UNKNOWN')
    if (not device_id or device_id != expected.device_id
            or type(expected.pid) is not int or expected.pid <= 0
            or type(expected.start_time_ns) is not int or expected.start_time_ns <= 0):
        return unknown
    observed = read_windows_process_identity(expected.pid)
    if observed is None or observed.start_time_ns != expected.start_time_ns:
        return unknown
    return ProcessStatus(device_id, expected.pid, expected.start_time_ns, observed.state)
