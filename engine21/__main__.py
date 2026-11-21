"""Host-facing local entry point. No signing, privilege changes or auto-merge."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from . import runner,state


def main(argv=None)->int:
    p=argparse.ArgumentParser(description='Film Review Agent 2.1 controlled local execution')
    subs=p.add_subparsers(dest='command',required=True)
    init=subs.add_parser('init',help='Pin trusted adapter config and start a state ledger')
    init.add_argument('--job',type=Path,required=True)
    init.add_argument('--config',type=Path,required=True)
    inspect=subs.add_parser('inspect',help='Read and revalidate current engine state')
    inspect.add_argument('--job',type=Path,required=True)
    go=subs.add_parser('run',help='Execute one configured stage; no autonomous cascade')
    go.add_argument('--job',type=Path,required=True)
    go.add_argument('--config',type=Path,required=True)
    go.add_argument('--stage',choices=state.STAGES,required=True)
    go.add_argument('--receipts-dir',type=Path)
    go.add_argument('--host-key-file',type=Path)
    go.add_argument('--rerun-stale',action='store_true')
    args=p.parse_args(argv)
    try:
        if args.command=='init':
            runner.adapter_config(args.config)
            result=state.load_or_init(args.job,args.config)
        elif args.command=='inspect':
            result=state.reconcile(args.job)
        else:
            key=args.host_key_file.read_bytes() if args.host_key_file else None
            result=runner.run(args.job,args.config,args.stage,
                              receipts_dir=args.receipts_dir,key=key,rerun_stale=args.rerun_stale)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result.get('status')!='FAILED' else 1
    except (ValueError,PermissionError,OSError,KeyError,json.JSONDecodeError) as exc:
        print(json.dumps({'error':type(exc).__name__,'message':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
