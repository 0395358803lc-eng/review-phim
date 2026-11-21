#!/usr/bin/env python3
"""Single-stage Engine21 worker. Never runs provider commands via shell."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from stage3.framework import run_stage,runtime_digest

def main(argv=None)->int:
    parser=argparse.ArgumentParser(description="Controlled film stage adapter; synthetic is explicit")
    parser.add_argument("--mode",required=True,choices=["synthetic","production"])
    parser.add_argument("--provider-config",type=Path)
    parser.add_argument("--runtime-sha256",required=True,
                        help="Trusted host-pinned SHA256 over adapter + all stage3 modules")
    args=parser.parse_args(argv)
    try:
        if runtime_digest()!=args.runtime_sha256:
            raise ValueError("Stage 3 runtime package checksum mismatch; refuse execution")
        result=run_stage(mode=args.mode,environ=os.environ,provider_config=args.provider_config)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,RuntimeError,KeyError,TimeoutError) as exc:
        print(json.dumps({"error":type(exc).__name__,"reason":str(exc),
                          "synthetic_mode":args.mode=="synthetic"}),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
