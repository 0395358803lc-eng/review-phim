"""Bounded adapter runner: no shell, new output directory each attempt."""
from __future__ import annotations
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import subprocess

from . import state, gates


def adapter_config(path:Path) ->dict:
    config=json.loads(Path(path).read_text(encoding='utf8'))
    if config.get('schema_version')!='2.1.0' or not isinstance(config.get('stages'),dict):
        raise ValueError('Unsupported 2.1 adapter configuration')
    if not set(config['stages']).issubset(set(state.STAGES)):
        raise ValueError('Adapter configuration includes unknown stage')
    for stage, spec in config['stages'].items():
        if not isinstance(spec,dict):
            raise ValueError(f'{stage} adapter must be an object')
        executable=Path(str(spec.get('executable','')))
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError(f'{stage} executable must be an existing absolute file')
        argv=spec.get('argv')
        if (not isinstance(argv,list) or any(not isinstance(s,str) for s in argv)
            or not argv or any('\x00' in s for s in argv)):
            raise ValueError(f'{stage} adapter arguments must be a nonempty argv array')
        timeout=spec.get('timeout_seconds',0)
        maximum=spec.get('max_attempts',0)
        if not isinstance(timeout,(int,float)) or isinstance(timeout,bool) or not 1<=timeout<=3600:
            raise ValueError('Adapter timeout must be 1-3600 seconds')
        if not isinstance(maximum,int) or isinstance(maximum,bool) or not 1<=maximum<=3:
            raise ValueError('Adapter max_attempts must be 1-3')
        if not isinstance(spec.get('retry_safe'),bool):
            raise ValueError('Adapter retry_safe must be explicitly boolean')
        digest=spec.get('executable_sha256')
        if digest is not None and state.sha256(executable)!=digest:
            raise ValueError('Adapter executable SHA256 changed')
    return config


def _fingerprints(spec:dict)->list[dict]:
    names=[spec['executable']]
    names.extend(x for x in spec['argv'] if Path(x).is_absolute() and Path(x).is_file())
    return [{'path':p,'sha256':state.sha256(Path(p))} for p in names]


def _command(spec:dict,values:dict)->list[str]:
    args=[]
    for raw in spec['argv']:
        substituted=raw
        for name,value in values.items():
            substituted=substituted.replace('{'+name+'}',str(value))
        if re.search(r'\{[a-zA-Z_]+\}',substituted):
            raise ValueError('Unknown substitution in argv')
        args.append(substituted)
    return [spec['executable']]+args


def run(job:Path, config_path:Path, stage:str, *,receipts_dir:Path|None=None,
        key:bytes|None=None, rerun_stale:bool=False)->dict:
    job=Path(job).resolve(strict=True)
    if stage not in state.REQUIRES:
        raise ValueError('Unknown N00-N09 stage')
    config=adapter_config(config_path)
    if stage not in config['stages']:
        raise ValueError('No configured adapter for '+stage)
    spec=config['stages'][stage]
    with state.exclusive(job):
        s=state.init_locked(job,Path(config_path))
        s=state.reconcile_locked(job,s)
        if not s['source_intact']:
            raise ValueError('Original movie SHA256 changed; refuse execution')
        current=s['stages'][stage]
        status=current['status']
        if status=='DONE':
            return {'stage':stage,'status':'ALREADY_DONE','attempts':current['attempts']}
        if status=='STALE' and not rerun_stale:
            raise ValueError('Output stale; require explicit --rerun-stale authorization')
        if status in ('STALE','INTERRUPTED','FAILED') and not spec['retry_safe']:
            raise ValueError('Unsafe retry blocked; operator must create a new revision')
        if any(s['stages'][dep]['status']!='DONE' for dep in state.REQUIRES[stage]):
            raise ValueError('Required prerequisite N00-N09 stage is not DONE and valid')
        if status in ('FAILED','STALE','INTERRUPTED') and current['attempts']>=spec['max_attempts']:
            raise ValueError('Bounded retry budget exceeded; start a new revision')
        inputs=_fingerprints(spec)
        if current.get('adapter_inputs_sha256') and current['adapter_inputs_sha256']!=inputs:
            raise ValueError('Adapter implementation changed since last attempt')
        gates.check_approvals(job,s,stage,receipts_dir,key)
        attempt_no=current['attempts']+1
        output_dir=job/'.engine21'/'attempts'/stage/f'{attempt_no:04d}'
        output_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
        current.update(status='RUNNING',attempts=attempt_no,
                       adapter_inputs_sha256=inputs,started_at_utc=datetime.now(timezone.utc).isoformat(),
                       evidence_path=None,evidence_sha256=None,artifacts=[])
        state.atomic_state(job,s)
        values={'job':job,'stage':stage,'output_dir':output_dir,
                'source':state.job_details(job)['source']['absolute_path'],
                'source_sha256':s['source_sha256']}
        command=_command(spec,values)
        env={k:v for k,v in os.environ.items() if k.upper() in {
             'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','HOME','LANG','LC_ALL','PYTHONPATH'}}
        env.update({'FRA_JOB':str(job),'FRA_STAGE':stage,
                    'FRA_OUTPUT_DIR':str(output_dir),
                    'FRA_SOURCE':str(values['source']),
                    'FRA_SOURCE_SHA256':s['source_sha256'],
                    'FRA_REQUIRED_CHECKS':json.dumps(state.CHECKS[stage]),
                    'FRA_REQUIRED_OUTPUTS':json.dumps(state.REQUIRED_OUTPUTS[stage])})
        stdout=output_dir/'stdout.log'
        stderr=output_dir/'stderr.log'
        exit_code=None
        problem=None
        for retry in range(attempt_no,spec['max_attempts']+1):
            if retry!=attempt_no:
                output_dir=job/'.engine21'/'attempts'/stage/f'{retry:04d}'
                output_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
                values['output_dir']=output_dir
                command=_command(spec,values)
                env['FRA_OUTPUT_DIR']=str(output_dir)
                stdout=output_dir/'stdout.log';stderr=output_dir/'stderr.log'
                current['attempts']=retry
                state.atomic_state(job,s)
            try:
                with stdout.open('wb') as fout, stderr.open('wb') as ferr:
                    p=subprocess.run(command,cwd=output_dir,env=env,
                         stdout=fout,stderr=ferr,timeout=spec['timeout_seconds'],check=False)
                exit_code=p.returncode
                if p.returncode:
                    raise ValueError(f'Adapter exit status {p.returncode}')
                if not state.source_valid(job) or state.job_details(job)['source']['sha256']!=s['source_sha256']:
                    raise ValueError('Original source changed while adapter was running')
                if state.sha256(Path(config_path))!=s['config_sha256']:
                    raise ValueError('Trusted config changed while adapter was running')
                if _fingerprints(spec)!=inputs:
                    raise ValueError('Adapter inputs changed while running')
                gates.check_approvals(job,s,stage,receipts_dir,key)
                doc,artifacts=gates.verify_evidence(job,stage,output_dir,s['source_sha256'])
                ep=output_dir/'evidence.json'
                current.update(status='DONE', evidence_path=str(ep.relative_to(job)),
                               evidence_sha256=state.sha256(ep),artifacts=artifacts,
                               completed_at_utc=datetime.now(timezone.utc).isoformat(),
                               stdout_sha256=state.sha256(stdout),stderr_sha256=state.sha256(stderr))
                state.atomic_state(job,s)
                return {'stage':stage,'status':'DONE','attempts':current['attempts'],
                        'artifacts':artifacts,'evidence_path':current['evidence_path']}
            except (ValueError,OSError,subprocess.TimeoutExpired) as exc:
                problem=str(exc)
                current.update(status='FAILED',reason=problem,
                               completed_at_utc=datetime.now(timezone.utc).isoformat())
                state.atomic_state(job,s)
                if not spec['retry_safe'] or retry>=spec['max_attempts']:
                    break
        return {'stage':stage,'status':'FAILED','attempts':current['attempts'],
                'exit_code':exit_code,'reason':problem}
