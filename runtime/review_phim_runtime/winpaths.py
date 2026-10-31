"""Windows source-path canonicalization for existing local files only.

This refuses remote/UNC, device namespace, alternate data streams, and
ambiguous components. Permission checks must follow canonicalization and a
host implementation must bind the verified file handle before use to avoid
TOCTOU between verification and opening the target.
"""
import ntpath
import os
from typing import Callable


def _validate_local_drive_path(path: str) -> None:
    if not isinstance(path, str) or not path or '\x00' in path:
        raise ValueError('Invalid path')
    path = path.replace('/', '\\')
    drive, tail = ntpath.splitdrive(path)
    if (len(drive) != 2 or drive[1:] != ':' or not drive[0].isalpha()
            or not tail.startswith('\\') or path.startswith('\\\\')):
        raise ValueError('Only fully-qualified local Windows drive paths are permitted')
    for component in tail.split('\\'):
        if component in ('.', '..') or ':' in component or (component and component[-1] in '. '):
            raise ValueError('Ambiguous Windows path component')


def canonical_windows_path(path: str, *, realpath: Callable[[str], str] | None = None) -> str:
    """Resolve an existing path; on non-Windows, only an injected test resolver is allowed."""
    _validate_local_drive_path(path)
    if realpath is None:
        if os.name != 'nt':
            raise RuntimeError('Windows host required')
        realpath = lambda p: os.path.realpath(p, strict=True)
    try:
        final_path = realpath(path)
        _validate_local_drive_path(final_path)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ValueError('Could not verify canonical path') from exc
    return ntpath.normpath(final_path)
