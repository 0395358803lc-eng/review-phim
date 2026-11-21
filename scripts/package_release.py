#!/usr/bin/env python3
"""Create a source-only Agent runtime ZIP. Never include tests or old film data."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import tempfile
import zipfile

from install_agent_runtime import ROOT, source_manifest

PACKAGE_ROOT = "film-review-runtime-2.1"

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()

def package(output: Path) -> dict:
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing ZIP: "+str(output))
    if not output.parent.is_dir():
        raise FileNotFoundError("Output parent directory missing")
    files = sorted(set(source_manifest(ROOT) + ["scripts/install_agent_runtime.py"]))
    if any(p.startswith(("tests/", "docs/qa/", "docs/superpowers/"))
           or any("synthetic" in p.lower() for p in (path,))
           or p.startswith("qa/legacy_offline_worker")
           for p in files for path in [p]):
        raise ValueError("Source-only manifest unexpectedly includes QA/test data")
    checksums = {p: digest(ROOT / p) for p in files}
    manifest = "".join(f"{h}  {p}\n" for p,h in checksums.items())
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in files:
            z.write(ROOT / path, arcname=PACKAGE_ROOT+"/"+path)
        z.writestr(PACKAGE_ROOT+"/SHA256SUMS.txt", manifest)
    with zipfile.ZipFile(output, "r") as z:
        if z.testzip() is not None:
            raise ValueError("Corrupted ZIP entry")
        actual = z.namelist()
        expected = [PACKAGE_ROOT+"/"+p for p in files]+[PACKAGE_ROOT+"/SHA256SUMS.txt"]
        if sorted(actual)!=sorted(expected):
            raise ValueError("Archive does not match allowlist")
        with tempfile.TemporaryDirectory() as temp:
            z.extractall(temp)
            directory = Path(temp)/PACKAGE_ROOT
            for relative, h in checksums.items():
                if digest(directory/relative)!=h:
                    raise ValueError("Extracted SHA256 differs: "+relative)
    return {"status":"SOURCE_ONLY_ZIP_VERIFIED",
            "zip":str(output),"zip_sha256":digest(output),
            "source_files":len(files),"test_files":0,"user_media_files":0,
            "old_movie_data":False}

def main() -> int:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--output",type=Path,default=ROOT.parent/"film-review-runtime-2.1-source-only.zip")
    opts=args.parse_args()
    import json
    print(json.dumps(package(opts.output),ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
