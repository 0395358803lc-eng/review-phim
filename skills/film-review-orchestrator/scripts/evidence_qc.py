#!/usr/bin/env python3
"""Independent semantic mapping invariants; not an AI truth oracle."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys

VERDICTS = {"VISUAL_DIRECT", "DIALOGUE_SUPPORTED", "CONTEXT_ONLY", "UNRESOLVED", "CONTRADICTED"}


def valid_number(value) -> bool:
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def validate_map(doc: dict) -> list[str]:
    problems: list[str] = []
    if not isinstance(doc, dict):
        return ["Root must be an object"]
    filmhash = doc.get("source_movie_sha256")
    if not isinstance(filmhash, str) or len(filmhash) != 64 or any(x not in "0123456789abcdef" for x in filmhash.lower()):
        problems.append("source_movie_sha256 must be SHA256 hex")
    film_dur = doc.get("source_duration_s")
    voice_dur = doc.get("narration_duration_s")
    if not valid_number(film_dur) or film_dur <= 0:
        problems.append("source_duration_s must be positive finite number")
        film_dur = None
    if not valid_number(voice_dur) or voice_dur <= 0:
        problems.append("narration_duration_s must be positive finite number")
        voice_dur = None
    sentences = doc.get("sentences")
    if not isinstance(sentences, list) or not sentences:
        return problems + ["sentences must be nonempty array"]
    ids = set()
    ordered = []
    for i, s in enumerate(sentences):
        k = f"sentences[{i}]"
        if not isinstance(s, dict):
            problems.append(f"{k} must be an object")
            continue
        sid = s.get("sentence_id")
        if not isinstance(sid, str) or not sid:
            problems.append(f"{k}.sentence_id missing")
        elif sid in ids:
            problems.append(f"{k}.sentence_id duplicate")
        ids.add(sid)
        if not isinstance(s.get("review_text"), str) or not s["review_text"].strip():
            problems.append(f"{k}.review_text empty")
        start, end = s.get("voice_start_s"), s.get("voice_end_s")
        sentence_time_ok = valid_number(start) and valid_number(end) and 0 <= start < end
        if not sentence_time_ok or (voice_dur is not None and end > voice_dur + 0.045):
            problems.append(f"{k}.voice timeline invalid")
        else:
            ordered.append((start, end, sid))
        claims = s.get("atomic_claims")
        if not isinstance(claims, list) or not claims:
            problems.append(f"{k}.atomic_claims missing")
            claims = []
        unresolved = s.get("unresolved_claims", [])
        if not isinstance(unresolved, list):
            problems.append(f"{k}.unresolved_claims must be list")
            unresolved = []
        claim_ids = set()
        for j, claim in enumerate(claims):
            if not isinstance(claim, dict):
                problems.append(f"{k}.claim[{j}] invalid")
                continue
            claim_ids.add(claim.get("claim_id"))
            v = claim.get("verdict")
            if v not in VERDICTS:
                problems.append(f"{k}.claim[{j}] invalid verdict")
            evid = claim.get("evidence_ids", [])
            if v in {"VISUAL_DIRECT", "DIALOGUE_SUPPORTED"} and (not isinstance(evid, list) or not evid):
                problems.append(f"{k}.claim[{j}] asserted without visual/ASR evidence")
            if v == "UNRESOLVED" and claim.get("claim_id") not in unresolved:
                problems.append(f"{k}.claim[{j}] unresolved not disclosed")
            if v == "CONTRADICTED":
                problems.append(f"{k}.claim[{j}] contradicted; must revise script or stop")
        if any(c not in claim_ids for c in unresolved):
            problems.append(f"{k} unresolved_claims refer to absent claim")
        shots = s.get("chosen_shots")
        if not isinstance(shots, list) or not shots:
            problems.append(f"{k}.chosen_shots missing: unresolved placeholder still required")
            continue
        shot_visual_ids = set()
        shot_asr_ids = set()
        for shot in shots:
            if isinstance(shot, dict):
                if isinstance(shot.get("visual_evidence_ids"), list):
                    shot_visual_ids.update(shot["visual_evidence_ids"])
                if isinstance(shot.get("asr_evidence_ids"), list):
                    shot_asr_ids.update(shot["asr_evidence_ids"])
        for j, claim in enumerate(claims):
            if not isinstance(claim, dict):
                continue
            ids = claim.get("evidence_ids")
            if not isinstance(ids, list):
                continue
            if claim.get("verdict") == "VISUAL_DIRECT" and not (set(ids) & shot_visual_ids):
                problems.append(f"{k}.claim[{j}] claim evidence not linked to chosen visual shots")
            if claim.get("verdict") == "DIALOGUE_SUPPORTED" and not (set(ids) & shot_asr_ids):
                problems.append(f"{k}.claim[{j}] claim evidence not linked to chosen ASR shots")
        for j, shot in enumerate(shots):
            tag = f"{k}.chosen_shots[{j}]"
            if not isinstance(shot, dict):
                problems.append(f"{tag} must be an object")
                continue
            a, b = shot.get("source_start_s"), shot.get("source_end_s")
            if not valid_number(a) or not valid_number(b) or a < 0 or a >= b or (film_dur is not None and b > film_dur + 0.001):
                problems.append(f"{tag} outside source_duration_s or zero length")
            x, y = shot.get("voice_start_s"), shot.get("voice_end_s")
            if not valid_number(x) or not valid_number(y) or x < 0 or x >= y or (sentence_time_ok and (x < start - 0.045 or y > end + 0.045)):
                problems.append(f"{tag} outside sentence voice duration")
            v = shot.get("verdict")
            if v not in VERDICTS:
                problems.append(f"{tag} invalid verdict")
            vis = shot.get("visual_evidence_ids", [])
            asr = shot.get("asr_evidence_ids", [])
            if v == "VISUAL_DIRECT" and (not isinstance(vis, list) or not vis):
                problems.append(f"{tag} VISUAL_DIRECT missing frame evidence")
            if v == "DIALOGUE_SUPPORTED" and (not isinstance(asr, list) or not asr):
                problems.append(f"{tag} DIALOGUE_SUPPORTED missing ASR evidence")
            if v in {"UNRESOLVED", "CONTRADICTED"}:
                problems.append(f"{tag} has unsupported/contradicted scene; do not render it")
            if not isinstance(shot.get("qualifier", ""), str):
                problems.append(f"{tag}.qualifier must be text")
    if any(a >= b for (a, _, _), (b, _, _) in zip(ordered, ordered[1:])):
        problems.append("sentences must be in ascending voice time")
    return problems


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Check narration-to-source evidence map, not semantic truth")
    p.add_argument("--map", required=True, type=Path)
    a = p.parse_args(argv)
    problems = validate_map(json.loads(a.map.read_text(encoding="utf-8")))
    if problems:
        for x in problems:
            print("FAIL:", x, file=sys.stderr)
        return 2
    print("PASS: mapping structure, source ranges and evidence labels (manual content verification still required)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
