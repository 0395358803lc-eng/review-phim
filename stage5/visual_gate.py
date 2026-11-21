"""Fail-closed Qwen check on CLIP-proposed source frames.

A Qwen YES only gives TENTATIVE evidence and never authorizes production.
Claim IDs and frame SHA/timecodes cannot be substituted by similarity score.
"""
from __future__ import annotations
import hashlib
import math
import re
from .translation import HEX64, EVIDENCE_ID

_MOTION_TERMS=re.compile(r"(?i)\b(fir(?:e|es|ing|ed)\s+(?:a\s+)?(?:gun|rifle)|killed?|shooting|shoots?|stole|steals?|murder(?:ed|s|ing)?|explod(?:e|ing|ed))\b|nổ súng|đánh cắp|bắn chết|giết người")

def select_visual_shot(source_sha256:str,claim:dict,
                       clip_candidates:list[dict],qwen_verdicts:list[dict],
                       source_duration_s:float)->dict:
    if not isinstance(source_sha256,str) or not HEX64.fullmatch(source_sha256):
        raise ValueError("Invalid source movie SHA")
    if type(source_duration_s) not in (int,float) or not math.isfinite(source_duration_s) or source_duration_s<=0:
        raise ValueError("Invalid source movie duration")
    if not isinstance(claim,dict) or claim.get("source_sha256")!=source_sha256:
        raise ValueError("Claim source SHA mismatch")
    cid=claim.get("claim_id")
    if not isinstance(cid,str) or not EVIDENCE_ID.fullmatch(cid):
        raise ValueError("Invalid claim ID")
    evid=claim.get("evidence_ids")
    if (not isinstance(evid,list) or not evid
        or any(not isinstance(x,str) or not EVIDENCE_ID.fullmatch(x) for x in evid)):
        raise ValueError("Claim evidence IDs invalid")
    if not isinstance(claim.get("text"),str) or not claim["text"].strip():
        raise ValueError("Missing claim text")
    if claim.get("verdict") not in ("VISUAL_DIRECT","DIALOGUE_SUPPORTED"):
        raise ValueError("Unresolved claim cannot be selected")
    if not isinstance(clip_candidates,list) or not clip_candidates:
        raise ValueError("CLIP candidates missing")
    if not isinstance(qwen_verdicts,list):
        raise ValueError("Qwen verdicts invalid")
    # Check *all* candidate metadata before any selection; a stray out-of-range
    # or foreign-movie frame must fail the whole operation.
    candidates={}
    previous=float("inf")
    for rank,c in enumerate(clip_candidates,1):
        if not isinstance(c,dict):
            raise ValueError("Malformed CLIP candidate")
        frame=c.get("frame_id")
        if not isinstance(frame,str) or not EVIDENCE_ID.fullmatch(frame) or frame in candidates:
            raise ValueError("Duplicate or invalid frame ID")
        if c.get("source_sha256")!=source_sha256:
            raise ValueError("Candidate frame source SHA mismatch")
        if not isinstance(c.get("frame_sha256"),str) or not HEX64.fullmatch(c["frame_sha256"]):
            raise ValueError("Candidate frame SHA missing")
        s,e=c.get("start_s"),c.get("end_s")
        if (type(s) not in (int,float) or type(e) not in (int,float) or
            not math.isfinite(s) or not math.isfinite(e) or
            not 0<=s<e<=source_duration_s+0.001):
            raise ValueError("CLIP candidate time outside movie")
        score=c.get("raw_cosine")
        if (type(score) not in (int,float) or not math.isfinite(score)
            or not -1.0001<=score<=1.0001):
            raise ValueError("Invalid raw CLIP cosine")
        if score>previous+1e-7:
            raise ValueError("CLIP candidates not ranked by score")
        previous=score
        candidates[frame]=(c,rank)
    verdicts={}
    for q in qwen_verdicts:
        if not isinstance(q,dict) or q.get("claim_id")!=cid:
            raise ValueError("Qwen verdict claim mismatch")
        frame=q.get("frame_id")
        if frame not in candidates or frame in verdicts:
            raise ValueError("Qwen unknown or duplicate frame ID")
        original=candidates[frame][0]
        if q.get("human_approved") not in (None,False):
            raise ValueError("Qwen model cannot provide human approval")
        if q.get("claim_text_sha256")!=hashlib.sha256(claim["text"].encode("utf8")).hexdigest():
            raise ValueError("Qwen verified a different claim text; refuse claim substitution")
        if q.get("source_sha256")!=source_sha256:
            raise ValueError("Qwen verdict source movie mismatch")
        if q.get("frame_sha256")!=original["frame_sha256"]:
            raise ValueError("Qwen candidate frame SHA mismatch")
        if q.get("verdict") not in ("YES","NO","UNCERTAIN"):
            raise ValueError("Malformed Qwen verdict")
        if not isinstance(q.get("provider"),str) or not q["provider"].strip():
            raise ValueError("Qwen provider provenance absent")
        verdicts[frame]=q
    result={"schema_version":"5.0","source_sha256":source_sha256,
       "original_claim_id":cid,"original_claim_text":claim["text"],
       "original_evidence_ids":evid[:],
       "status":"UNRESOLVED","selected_frame_id":None,"clip_rank":None,
       "source_interval_s":None,"frame_sha256":None,
       "qwen_visual_verdict":None,
       "audit":[{"frame_id":k,"clip_rank":v[1],
                 "raw_cosine":float(v[0]["raw_cosine"]),
                 "qwen_verdict":verdicts.get(k,{}).get("verdict","MISSING")}
                 for k,v in candidates.items()],
       "approved_for_render":False,"human_visual_review_required":True,
       "claim_truth_certified":False}
    if claim["verdict"]=="DIALOGUE_SUPPORTED":
        result.update(status="DIALOGUE_ONLY",reason="Dialogue text cannot prove an object is visible")
        return result
    if claim.get("requires_motion") is True or _MOTION_TERMS.search(claim["text"]):
        result["reason"]="Single still does not verify temporal action"
        return result
    for k,(candidate,rank) in candidates.items():
        if k not in evid:
            continue
        verified=verdicts.get(k)
        if verified is not None and verified["verdict"]=="YES":
            result.update(status="TENTATIVE_VISUAL_CANDIDATE",
                selected_frame_id=k,clip_rank=rank,
                source_interval_s=[float(candidate["start_s"]),float(candidate["end_s"])],
                frame_sha256=candidate["frame_sha256"],
                qwen_visual_verdict="YES",
                reason="CLIP proposed and Qwen answered YES; not human verification")
            return result
    result["reason"]="No evidence-bound source frame with a Qwen YES; fail closed"
    return result
