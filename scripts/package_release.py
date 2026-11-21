#!/usr/bin/env python3
"""Build a standalone ZIP without cache/media and verify checksums after extraction."""
from __future__ import annotations
import hashlib
from pathlib import Path
import shutil
import tempfile
import zipfile
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / (ROOT.name + ".zip")
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".git"}
EXCLUDED_SUFFIX = {".pyc", ".tmp", ".swp"}


def filehash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not set(p.parts) & EXCLUDED_PARTS and p.suffix not in EXCLUDED_SUFFIX and p.name != 'MANIFEST.sha256')


def main():
    entries = [(filehash(p), p.relative_to(ROOT).as_posix()) for p in files()]
    (ROOT / 'MANIFEST.sha256').write_text(''.join(f'{digest}  {name}\n' for digest,name in entries),encoding='utf-8')
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files() + [ROOT / 'MANIFEST.sha256']:
            z.write(p, arcname=f'{ROOT.name}/{p.relative_to(ROOT).as_posix()}')
    with zipfile.ZipFile(OUT) as z:
        if z.testzip() is not None:
            raise RuntimeError('Corrupted ZIP member')
        names=z.namelist()
        if any('__pycache__' in n or n.endswith('.mp4') or n.endswith('.wav') for n in names):
            raise RuntimeError('Release contains cache or user media')
        with tempfile.TemporaryDirectory() as tmp:
            z.extractall(tmp)
            extracted = Path(tmp) / ROOT.name
            for digest,name in entries:
                if filehash(extracted/name)!=digest:
                    raise RuntimeError('SHA256 mismatch after extract: '+name)
            if not (extracted/'skills/film-review-orchestrator/SKILL.md').is_file():
                raise RuntimeError('Skill not discoverable in ZIP')
    print(f'OK ZIP: {OUT} bytes={OUT.stat().st_size} files={len(entries)+1} sha256={filehash(OUT)}')

if __name__ == '__main__':
    main()
