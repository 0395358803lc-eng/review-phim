"""Fail-closed approval and evidence validation.

Receipts must originate from an external trusted host; DO NOT expose a signer
or its secret to the model/agent. signed_receipt is test-only helper, not CLI.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import shutil
import subprocess

from . import state


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(',',':')).encode('utf8')


def verify_receipt(receipt: dict, gate: str, job_id: str, subject_sha256: str,
                   key: bytes) -> bool:
    if not isinstance(key, bytes) or len(key) < 16:
        raise ValueError('Trusted approval key not available or too short')
    fields=('job_id','gate','subject_sha256','issued_at_utc','expires_at_utc')
    if not isinstance(receipt,dict) or set(receipt) != set(fields)|{'signature'}:
        raise ValueError('Malformed approval receipt')
    if (receipt['job_id'],receipt['gate'],receipt['subject_sha256']) != (job_id,gate,subject_sha256):
        raise ValueError('Approval subject, job or gate mismatch')
    if not re.fullmatch('[0-9a-f]{64}',subject_sha256):
        raise ValueError('Invalid approval subject hash')
    try:
        issued=datetime.fromisoformat(receipt['issued_at_utc'].replace('Z','+00:00'))
        expiry=datetime.fromisoformat(receipt['expires_at_utc'].replace('Z','+00:00'))
    except (ValueError,AttributeError):
        raise ValueError('Invalid approval timestamp') from None
    now=datetime.now(timezone.utc)
    if issued.tzinfo is None or expiry.tzinfo is None:
        raise ValueError('Approval time must have UTC offset')
    if issued > now+timedelta(seconds=30) or expiry < now or expiry <= issued:
        raise ValueError('Approval not yet issued or expired')
    fields_to_sign={field:receipt[field] for field in fields}
    expected=hmac.new(key,_canonical(fields_to_sign),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,str(receipt['signature'])):
        raise ValueError('Approval signature invalid')
    return True


def _subject(job: Path, obj:dict, gate:str) -> str:
    if gate == 'script':
        completed=obj['stages']['N05']
        if completed['status']!='DONE':
            raise PermissionError('Review script not yet completed')
        return completed['evidence_sha256']
    if gate == 'voice':
        sample=state.inside_job(job,'voice/approved_sample.wav')
        verify_media(sample,require_audio=True)
        return state.sha256(sample)
    if gate == 'pilot':
        pilot=state.inside_job(job,'edit/pilot.mp4')
        verify_media(pilot, require_audio=True, require_video=True)
        return state.sha256(pilot)
    raise ValueError('Unknown approval gate')


def check_approvals(job: Path,obj:dict,stage:str,receipts_dir:Path|None,key:bytes|None)->None:
    gates = {'N06':('script','voice'), 'N08':('pilot',)}.get(stage,())
    if not gates:
        return
    if not key or receipts_dir is None:
        raise PermissionError('Trusted host key/approval receipts unavailable; approval-required stage blocked')
    for gate in gates:
        receipt_path=Path(receipts_dir)/f'{gate}.json'
        if not receipt_path.is_file():
            raise PermissionError(f'Actual host-signed {gate} approval missing')
        receipt=json.loads(receipt_path.read_text(encoding='utf8'))
        verify_receipt(receipt,gate,obj['job_id'],_subject(job,obj,gate),key)


def verify_media(path:Path, *,require_audio:bool=False,require_video:bool=False)->dict:
    """Full stream decode, not ffprobe-only, with bounded process exit."""
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'Media missing: {path}')
    if not shutil.which('ffprobe') or not shutil.which('ffmpeg'):
        raise ValueError('Independent ffmpeg/ffprobe unavailable')
    probe=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90,check=False)
    if probe.returncode:
        raise ValueError('ffprobe media inspection failed: '+probe.stderr[-250:])
    doc=json.loads(probe.stdout)
    kinds={s.get('codec_type') for s in doc.get('streams',[])}
    if require_video and 'video' not in kinds:
        raise ValueError('Missing video stream')
    if require_audio and 'audio' not in kinds:
        raise ValueError('Missing audio stream')
    decode=subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(path),
                           '-map','0:v?','-map','0:a?','-f','null','-'],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3600,check=False)
    if decode.returncode:
        raise ValueError('Full media decode failed: '+decode.stderr.decode('utf8','replace')[-300:])
    return {'streams': sorted(x for x in kinds if isinstance(x,str)),
            'duration':float(doc.get('format',{}).get('duration') or 0)}


def verify_evidence(job:Path,stage:str,attempt_dir:Path,source_sha256:str)->tuple[dict,list[dict]]:
    docpath=attempt_dir/'evidence.json'
    if not docpath.is_file():
        raise ValueError('Stage produced no evidence.json')
    doc=json.loads(docpath.read_text(encoding='utf8'))
    if doc.get('stage')!=stage or doc.get('outcome')!='PASS':
        raise ValueError('Wrong stage/outcome in evidence')
    if doc.get('source_sha256')!=source_sha256 or not doc.get('reviewed_at_utc'):
        raise ValueError('Source provenance or review time missing')
    checks=doc.get('checks',{})
    if any(checks.get(k) is not True for k in state.CHECKS[stage]):
        raise ValueError('Mandatory evidence checks missing; claims alone do not prove results')
    artifacts=doc.get('artifacts')
    if not isinstance(artifacts,list) or not artifacts:
        raise ValueError('Stage must deliver at least one real artifact')
    names={Path(str(item.get('path',''))).name for item in artifacts if isinstance(item,dict)}
    missing=set(state.REQUIRED_OUTPUTS[stage])-names
    if missing:
        raise ValueError('Missing required stage output: '+', '.join(sorted(missing)))
    for item in artifacts:
        if not isinstance(item,dict) or not isinstance(item.get('sha256'),str):
            raise ValueError('Bad artifact reference')
        actual=state.inside_job(job,item.get('path'))
        if not actual.is_relative_to(attempt_dir.resolve()):
            raise ValueError('Artifact does not belong to current attempt')
        if not actual.is_file() or actual.stat().st_size==0 or state.sha256(actual)!=item['sha256']:
            raise ValueError('Artifact absent, empty or checksum differs')
        if actual.suffix in ('.json','.jsonl'):
            with actual.open(encoding='utf8') as f:
                if actual.suffix=='.json':
                    if not isinstance(json.load(f),(dict,list)):
                        raise ValueError('Invalid stage JSON structure')
                else:
                    for line in f:
                        if line.strip(): json.loads(line)
    if stage=='N00':
        manifests=[state.inside_job(job,a['path']) for a in artifacts if Path(a['path']).name=='source_manifest.json']
        if len(manifests)!=1 or json.loads(manifests[0].read_text(encoding='utf8')).get('source_sha256')!=source_sha256:
            raise ValueError('N00 source_manifest source hash mismatch')
        media=Path(state.job_details(job)['source']['absolute_path'])
        verify_media(media,require_video=True,require_audio=True)
    if stage in ('N06','N08','N09'):
        expected=('.wav',) if stage=='N06' else ('.mp4',)
        media=[state.inside_job(job,a['path']) for a in artifacts if str(a['path']).lower().endswith(expected)]
        if not media:
            raise ValueError('Required audio/video artifact not delivered')
        for p in media:
            verify_media(p,require_audio=True,require_video=stage!='N06')
    if stage=='N07':
        matches=[state.inside_job(job,a['path']) for a in artifacts if str(a['path']).endswith('sentence_shot_map.json')]
        if not matches:
            raise ValueError('N07 missing sentence_shot_map.json')
        import sys
        scripts=Path(__file__).resolve().parents[1]/'skills'/'film-review-orchestrator'/'scripts'
        sys.path.insert(0,str(scripts))
        import evidence_qc
        for p in matches:
            obj=json.loads(p.read_text(encoding='utf8'))
            if obj.get('source_movie_sha256')!=source_sha256 or evidence_qc.validate_map(obj):
                raise ValueError('Semantic source map not independently validated')
    return doc,artifacts
