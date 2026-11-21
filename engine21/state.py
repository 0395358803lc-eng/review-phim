"""Crash-safe local job state, artifact checks and DAG invalidation.

This does not mutate the 2.0 `job_state.json` or any 2.0 SKILL.md files.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import tempfile

STAGES = tuple(f'N{i:02}' for i in range(10))
REQUIRES = {
    'N00': (), 'N01': ('N00',), 'N02': ('N00',), 'N03': ('N01',),
    'N04': ('N02','N03'), 'N05': ('N04',), 'N06': ('N05',),
    'N07': ('N04','N06'), 'N08': ('N07',), 'N09': ('N08',),
}
REQUIRED_OUTPUTS = {
    'N00': ('source_manifest.json',),
    'N01': ('scenes.jsonl','frames.jsonl'),
    'N02': ('transcript_original.jsonl','transcript_vi.jsonl','uncertainties.jsonl'),
    'N03': ('visual_observations.jsonl','uncertain.jsonl'),
    'N04': ('story_timeline.json','event_claims.jsonl','unresolved.jsonl'),
    'N05': ('review_final.txt','sentence_claims.jsonl','evidence_ledger.jsonl'),
    'N06': ('narration.wav','sentence_audio_timeline.jsonl','audio_qc.json'),
    'N07': ('candidate_scenes.jsonl','sentence_shot_map.json','evidence_and_limits.jsonl'),
    'N08': ('pilot.mp4','timeline.json'),
    'N09': ('final_review.mp4','technical_qc.json','semantic_qc.json','delivery_manifest.json'),
}
CHECKS = {
    'N00': ('source_file_verified','media_probe_verified','decode_verified'),
    'N01': ('all_source_time_covered','source_scene_timestamp_verified'),
    'N02': ('asr_timestamp_in_range','unclear_speech_disclosed'),
    'N03': ('original_frames_checked','uncertain_visual_claims_labeled'),
    'N04': ('key_story_claims_traceable','conflicts_logged'),
    'N05': ('review_text_verified','atomic_claims_reconciled'),
    'N06': ('audio_render_verified','sentence_timing_verified'),
    'N07': ('all_sentences_have_decision','source_clips_traceable','unresolved_disclosed'),
    'N08': ('pilot_reviewed','chapter_media_decoded','narration_alignment_checked'),
    'N09': ('full_video_decoded','full_audio_decoded','provenance_rechecked','limitations_disclosed'),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inside_job(job: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('Absolute or blank artifact path')
    root = Path(job).resolve(strict=True)
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Artifact path escapes workspace')
    return path


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    with tempfile.NamedTemporaryFile('w', encoding='utf8', dir=path.parent,
                                     prefix='.pending-', delete=False) as f:
        tmp = Path(f.name)
        os.chmod(tmp, 0o600)
        f.write(serialized)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def job_details(job: Path) -> dict:
    job = Path(job).resolve(strict=True)
    obj = json.loads((job/'job_state.json').read_text(encoding='utf8'))
    if obj.get('schema_version') != '2.0.0' or not isinstance(obj.get('source'), dict):
        raise ValueError('Expected a Film Review Agent 2.0 job manifest')
    if set(obj.get('stages', {})) != set(STAGES):
        raise ValueError('Job stages do not match N00-N09')
    return obj


def source_valid(job: Path, details: dict | None = None) -> bool:
    src = (details or job_details(job))['source']
    path = Path(src['absolute_path'])
    return path.is_file() and path.stat().st_size == src['size_bytes'] and sha256(path) == src['sha256']


@contextmanager
def exclusive(job: Path):
    """Advisory lock released by OS even if the runner crashes. Linux/Windows."""
    jobroot = Path(job).resolve(strict=True)
    root = jobroot / '.engine21'
    if root.is_symlink() or (root.exists() and not root.resolve().is_relative_to(jobroot)):
        raise ValueError('Engine runtime folder may not be a symlink or escape the workspace')
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (root/'engine.lock').open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0'); handle.flush()
        try:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def state_path(job: Path) -> Path:
    return Path(job)/'.engine21'/'state.json'


def atomic_state(job: Path, obj: dict) -> None:
    atomic_write(state_path(job), obj)


def read_state(job: Path) -> dict:
    return json.loads(state_path(job).read_text(encoding='utf8'))


def init_locked(job: Path, config: Path) -> dict:
    details = job_details(job)
    config = Path(config).resolve(strict=True)
    if config.is_relative_to(Path(job).resolve(strict=True)):
        raise ValueError('Trusted adapter configuration must live OUTSIDE agent job workspace')
    fingerprint = sha256(config)
    file = state_path(job)
    if file.exists():
        obj = read_state(job)
        if obj.get('config_sha256') != fingerprint:
            raise ValueError('Adapter configuration differs from pinned SHA256; new revision required')
        if obj.get('source_sha256') != details['source']['sha256']:
            raise ValueError('Engine metadata and original source disagree')
        return obj
    obj = {'engine_version':'2.1.0', 'job_id':details['job_id'],
           'source_sha256':details['source']['sha256'], 'config_sha256':fingerprint,
           'created_at_utc':datetime.now(timezone.utc).isoformat(),
           'stages':{k:{'status':'PENDING','attempts':0,'artifacts':[],
                         'evidence_path':None,'evidence_sha256':None} for k in STAGES}}
    atomic_state(job,obj)
    return obj


def load_or_init(job: Path, config: Path) -> dict:
    with exclusive(job):
        return init_locked(job,config)


def _verified_stage(job: Path, record: dict) -> bool:
    try:
        if not record.get('evidence_path') or not record.get('evidence_sha256'):
            return False
        if sha256(inside_job(job,record['evidence_path'])) != record['evidence_sha256']:
            return False
        artifacts=record.get('artifacts',[])
        if not artifacts:
            return False
        for item in artifacts:
            if sha256(inside_job(job,item['path'])) != item['sha256']:
                return False
        return True
    except (ValueError,KeyError,OSError):
        return False


def reconcile_locked(job: Path, obj: dict) -> dict:
    # Verify the immutable engine source lock even if the 2.0 intake manifest was edited.
    if job_details(job)['source']['sha256'] != obj['source_sha256'] or not source_valid(job):
        for item in obj['stages'].values():
            if item['status'] == 'DONE':
                item['status'] = 'STALE'
        obj['source_intact'] = False
        atomic_state(job,obj)
        return obj
    obj['source_intact'] = True
    for stage in STAGES:
        item=obj['stages'][stage]
        if item['status']=='RUNNING':
            item['status']='INTERRUPTED'
            item['reason']='Previous process ended before evidence commit; rerun only if adapter retry_safe'
        if item['status']=='DONE':
            if any(obj['stages'][p]['status']!='DONE' for p in REQUIRES[stage]) or not _verified_stage(job,item):
                item['status']='STALE'
                item['reason']='Dependency or artifact/evidence checksum mismatch'
    atomic_state(job,obj)
    return obj


def reconcile(job: Path) -> dict:
    with exclusive(job):
        if not state_path(job).exists():
            raise ValueError('Engine not initialized: first run with --config')
        return reconcile_locked(job,read_state(job))
