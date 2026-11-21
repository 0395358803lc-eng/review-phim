"""Plan multiple original N05 claims and source shots; NOT an approved render."""
from __future__ import annotations
import math
from .translation import HEX64, EVIDENCE_ID

def _finite(x):
    return type(x) in (int,float) and math.isfinite(x)

def build_storyboard(source_sha256:str,source_duration_s:float,
                    sentences:list[dict],catalog:dict,selections:dict,
                    voice_timeline:list[dict]|None=None)->dict:
    if not isinstance(source_sha256,str) or not HEX64.fullmatch(source_sha256):
        raise ValueError("Invalid original source SHA")
    if not _finite(source_duration_s) or source_duration_s<=0:
        raise ValueError("Invalid original source duration")
    if not isinstance(sentences,list) or not sentences:
        raise ValueError("Missing source-grounded sentences")
    if not isinstance(catalog,dict) or not isinstance(selections,dict):
        raise ValueError("Missing source evidence catalog or selected shots")
    ids=[s.get("sentence_id") if isinstance(s,dict) else None for s in sentences]
    if any(not isinstance(x,str) or not EVIDENCE_ID.fullmatch(x) for x in ids) or len(set(ids))!=len(ids):
        raise ValueError("Duplicate or malformed sentence IDs")
    if set(ids)!=set(selections):
        raise ValueError("Shot selection sentence IDs differ from script")
    times={}
    if voice_timeline is not None:
        if not isinstance(voice_timeline,list):
            raise ValueError("Voice timeline not list")
        for t in voice_timeline:
            if not isinstance(t,dict):
                raise ValueError("Invalid voice timeline row")
            sid=t.get("sentence_id")
            st,end=t.get("voice_start_s"),t.get("voice_end_s")
            if not isinstance(sid,str) or sid in times or not _finite(st) or not _finite(end) or not 0<=st<end:
                raise ValueError("Malformed or duplicate voice timestamp")
            times[sid]=(float(st),float(end))
        if set(times)!=set(ids):
            raise ValueError("Voice timing sentence IDs differ from script")
    result=[]
    prev_voice_end=0.
    for s in sentences:
        sid=s["sentence_id"]
        if s.get("source_sha256")!=source_sha256:
            raise ValueError("Sentence source provenance mismatch")
        if not isinstance(s.get("review_text"),str) or not s["review_text"].strip():
            raise ValueError("Sentence review text missing")
        claims=s.get("atomic_claims")
        # One atomic claim per selected scene is required for now; compound
        # sentences MUST be split first rather than falsely imply one shot
        # proves two independent events.
        if not isinstance(claims,list) or len(claims)!=1:
            raise ValueError("Each storyboard shot must have one atomic claim; split compound sentences")
        claim=claims[0]
        if not isinstance(claim,dict) or claim.get("source_sha256")!=source_sha256:
            raise ValueError("Claim source SHA mismatch")
        if claim.get("verdict")!="VISUAL_DIRECT":
            raise ValueError("Unsupported nonvisual/unresolved claim cannot enter visual storyboard")
        claim_id=claim.get("claim_id")
        if not isinstance(claim_id,str) or not EVIDENCE_ID.fullmatch(claim_id):
            raise ValueError("Invalid original claim ID")
        sel=selections[sid]
        if not isinstance(sel,dict) or sel.get("status")!="TENTATIVE_VISUAL_CANDIDATE":
            raise ValueError("unresolved or nonvisual scene cannot be storyboarded")
        if sel.get("source_sha256")!=source_sha256 or sel.get("original_claim_id")!=claim_id:
            raise ValueError("Selection claim or source mismatch")
        eid=sel.get("selected_frame_id")
        if (not isinstance(eid,str) or eid not in catalog
            or eid not in claim.get("evidence_ids",[])):
            raise ValueError("Selection evidence does not support claim")
        evidence=catalog[eid]
        if evidence.get("source_sha256")!=source_sha256 or evidence.get("kind")!="visual":
            raise ValueError("Catalog source evidence is not visual from same movie")
        if claim.get("text")!=evidence.get("text"):
            raise ValueError("Original claim wording differs from source")
        start,end=evidence.get("start_s"),evidence.get("end_s")
        if not _finite(start) or not _finite(end) or not 0<=start<end<=source_duration_s+0.001:
            raise ValueError("Selected original source time out of range")
        clock=None
        if times:
            clock=times[sid]
            if clock[0]<prev_voice_end-0.001:
                raise ValueError("Overlapping/out-of-order supplied voice timeline")
            prev_voice_end=clock[1]
        result.append({"sentence_id":sid,"claim_id":claim_id,
                       "review_text":s["review_text"],
                       "source_sha256":source_sha256,
                       "source_evidence_id":eid,
                       "source_interval_s":[float(start),float(end)],
                       "proposed_voice_interval_s":list(clock) if clock else None,
                       "model_source_visual_verification":"QWEN_TENTATIVE_NOT_HUMAN",
                       "requires_human_scene_review":True})
    return {"schema_version":"5.0","source_sha256":source_sha256,
            "original_film_duration_s":float(source_duration_s),
            "shots":result,"sentence_count":len(result),
            "narration_duration_s":max(t[1] for t in times.values()) if times else None,
            "voice_timing_supplied":voice_timeline is not None,
            "voice_approval_required":True,"script_approval_required":True,
            "pilot_approval_required":True,"ready_to_render":False,
            "semantic_content_certified":False,
            "limitations":["Shot intervals anchor observed frames, not continuous event action",
                           "No full audio-to-scene synchronization without separately approved voice",
                           "Storyboard is not a release or a completed video"]}
