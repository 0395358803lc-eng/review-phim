#!/usr/bin/env python3
"""Portable local job registry: no AI/media work, no background execution.

The agent must supply real media and review evidence. A transition records
checks; it cannot independently certify that a human saw a scene or approved.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

VERSION = "2.0.0"
STAGES = [f"N{i:02}" for i in range(10)]
REQUIRES = {
    "N00": [], "N01": ["N00"], "N02": ["N00"],
    "N03": ["N01"], "N04": ["N02", "N03"], "N05": ["N04"],
    "N06": ["N05"], "N07": ["N04", "N06"],
    "N08": ["N07"], "N09": ["N08"],
}
APPROVAL_GATES = {"N05": "script", "N08": "pilot"}
STAGE_CHECKS = {
    "N00": ["source_file_verified", "media_probe_verified", "decode_verified"],
    "N01": ["all_source_time_covered", "source_scene_timestamp_verified"],
    "N02": ["asr_timestamp_in_range", "unclear_speech_disclosed"],
    "N03": ["original_frames_checked", "uncertain_visual_claims_labeled"],
    "N04": ["key_story_claims_traceable", "conflicts_logged"],
    "N05": ["review_text_verified", "atomic_claims_reconciled"],
    "N06": ["audio_render_verified", "sentence_timing_verified"],
    "N07": ["all_sentences_have_decision", "source_clips_traceable", "unresolved_disclosed"],
    "N08": ["pilot_reviewed", "chapter_media_decoded", "narration_alignment_checked"],
    "N09": ["full_video_decoded", "full_audio_decoded", "provenance_rechecked", "limitations_disclosed"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_slug(title: str) -> str:
    import unicodedata
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    title = re.sub(r"[^a-zA-Z0-9]+", "-", title).lower().strip("-")
    return title[:48] or "untitled-film"


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, prefix=".pending-") as f:
        f.write(data)
        tmp = Path(f.name)
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def probe_source(source: Path, ffprobe: str = "ffprobe") -> dict:
    cmd = [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(source)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"success": False, "error": f"ffprobe unavailable/timeout: {exc}"}
    if p.returncode:
        return {"success": False, "error": p.stderr[-1000:] or "ffprobe returned error"}
    try:
        result = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": "invalid ffprobe JSON"}
    return {"success": bool(result.get("streams")), "format": result.get("format", {}),
            "streams": result.get("streams", []), "note": "ffprobe does not prove full decode"}


def create_job(source: Path, workspace_root: Path, title: str, narration_language: str = "vi", *, probe: bool = True) -> Path:
    source = Path(source).expanduser().resolve(strict=True)
    if not source.is_file() or source.stat().st_size == 0:
        raise ValueError("Source must be a nonempty readable file")
    hash_value = sha256(source)
    root = Path(workspace_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    job_id = f"film-{safe_slug(title)}-{datetime.now(timezone.utc):%Y%m%d}-{hash_value[:12]}"
    job = root / job_id
    job.mkdir(mode=0o755, exist_ok=False)
    for folder in ("source", "ingest", "scenes", "speech", "vision", "story", "script",
                   "voice", "match", "edit", "qc", "delivery", "approvals", "evidence"):
        (job / folder).mkdir()
    state = {
        "schema_version": VERSION, "job_id": job_id, "created_at_utc": now(),
        "title": title, "narration_language": narration_language,
        "source": {"absolute_path": str(source), "sha256": hash_value,
                   "size_bytes": source.stat().st_size, "mtime_ns": source.stat().st_mtime_ns,
                   "is_external_original": True},
        "media_probe": probe_source(source) if probe else {"success": False, "error": "not run (synthetic/preflight)"},
        "stages": {key: {"status": "PENDING", "completed_at_utc": None, "evidence_relpath": None} for key in STAGES},
        "approvals": {}, "revisions": [], "delivery_status": "NOT_DELIVERED",
    }
    atomic_json(job / "job_state.json", state)
    atomic_json(job / "ingest" / "source_manifest.json", {
        "job_id": job_id, "source": state["source"], "media_probe": state["media_probe"],
        "original_movie_is_never_modified_by_jobctl": True,
    })
    return job


def read_job(job: Path) -> dict:
    path = Path(job) / "job_state.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != VERSION or set(data.get("stages", {})) != set(STAGES):
        raise ValueError("Unsupported or malformed job state")
    return data


def verify_source(job: Path) -> dict:
    state = read_job(job)
    original = Path(state["source"]["absolute_path"])
    if not original.is_file():
        return {"source_exists": False, "sha256_match": False, "original_path": str(original)}
    sha_match = sha256(original) == state["source"]["sha256"]
    size_match = original.stat().st_size == state["source"]["size_bytes"]
    return {"source_exists": True, "sha256_match": sha_match, "size_match": size_match,
            "original_path": str(original)}


def inside_job(job: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ValueError("Absolute or blank evidence path is not allowed")
    root = Path(job).resolve(strict=True)
    dest = (root / relative).resolve()
    if not dest.is_relative_to(root):
        raise ValueError("Evidence path escapes the job")
    return dest


def record_approval(job: Path, kind: str, reference: str, actor: str = "user") -> None:
    if kind not in {"script", "pilot", "voice"}:
        raise ValueError("Unknown approval kind")
    if actor != "user" or not reference or not reference.strip():
        raise ValueError("A real user approval reference is required; never invent one")
    state = read_job(job)
    existing = state["approvals"].get(kind)
    if existing:
        raise ValueError("Approval already recorded; use a new revision for changes")
    state["approvals"][kind] = {"actor": actor, "reference": reference.strip(), "recorded_at_utc": now()}
    atomic_json(Path(job) / "job_state.json", state)


def complete_stage(job: Path, stage: str, evidence_relpath: str) -> None:
    state = read_job(job)
    if stage not in REQUIRES:
        raise ValueError(f"Unknown stage: {stage}")
    if state["stages"][stage]["status"] == "DONE":
        raise ValueError("Stage already done; do not overwrite approved artifacts")
    for prereq in REQUIRES[stage]:
        if state["stages"][prereq]["status"] != "DONE":
            raise ValueError(f"Prerequisite {prereq} has not completed")
    if not verify_source(job)["sha256_match"]:
        raise ValueError("Source hash changed or source missing")
    approval = APPROVAL_GATES.get(stage)
    if approval and not state["approvals"].get(approval):
        raise ValueError(f"User {approval} approval reference missing")
    evidence_path = inside_job(job, evidence_relpath)
    if not evidence_path.is_file():
        raise ValueError("Stage evidence file does not exist")
    doc = json.loads(evidence_path.read_text(encoding="utf-8"))
    if doc.get("stage") != stage or doc.get("outcome") != "PASS":
        raise ValueError("Evidence stage/outcome mismatch")
    if doc.get("source_sha256") != state["source"]["sha256"]:
        raise ValueError("Evidence references a different source film")
    if not doc.get("reviewed_at_utc"):
        raise ValueError("Evidence missing review time")
    checks = doc.get("checks", {})
    if any(checks.get(check) is not True for check in STAGE_CHECKS[stage]):
        raise ValueError("Mandatory checks incomplete: " + ", ".join(k for k in STAGE_CHECKS[stage] if checks.get(k) is not True))
    files = doc.get("artifacts")
    if not isinstance(files, list) or not files:
        raise ValueError("No actual deliverable artifacts in evidence")
    for file in files:
        if not isinstance(file, dict) or not file.get("path") or not file.get("sha256"):
            raise ValueError("Artifact must include path and sha256")
        item = inside_job(job, file["path"])
        if not item.is_file() or sha256(item) != file["sha256"]:
            raise ValueError(f"Missing or changed artifact {file['path']}")
    state["stages"][stage] = {"status": "DONE", "completed_at_utc": now(),
                                "evidence_relpath": evidence_relpath, "evidence_sha256": sha256(evidence_path)}
    atomic_json(Path(job) / "job_state.json", state)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Film Review Agent V2 job control (no media processing)")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create isolated job and hash original")
    init.add_argument("--source", required=True, type=Path)
    init.add_argument("--workspace-root", required=True, type=Path)
    init.add_argument("--title", required=True)
    init.add_argument("--narration-language", default="vi")
    init.add_argument("--ffprobe", default="ffprobe")
    status = sub.add_parser("status")
    status.add_argument("--job", required=True, type=Path)
    verify = sub.add_parser("verify-source")
    verify.add_argument("--job", required=True, type=Path)
    approve = sub.add_parser("approve", help="Record an actual approval already received from the user")
    approve.add_argument("--job", required=True, type=Path)
    approve.add_argument("--gate", required=True, choices=["script", "pilot", "voice"])
    approve.add_argument("--reference", required=True)
    finish = sub.add_parser("complete-stage")
    finish.add_argument("--job", required=True, type=Path)
    finish.add_argument("--stage", required=True, choices=STAGES)
    finish.add_argument("--evidence", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            out = create_job(args.source, args.workspace_root, args.title, args.narration_language)
            print(json.dumps({"job": str(out), "media_probe": read_job(out)["media_probe"]}, ensure_ascii=False))
        elif args.command == "status":
            print(json.dumps(read_job(args.job), ensure_ascii=False, indent=2))
        elif args.command == "verify-source":
            print(json.dumps(verify_source(args.job), ensure_ascii=False, indent=2))
        elif args.command == "approve":
            record_approval(args.job, args.gate, args.reference)
            print("Approval reference recorded; actual origin must be independently verified")
        elif args.command == "complete-stage":
            complete_stage(args.job, args.stage, args.evidence)
            print(f"{args.stage} DONE: evidence and artifacts verified")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
