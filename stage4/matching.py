"""Bind actual N05 claims to N07 shots without losing evidence identity.

CLIP candidate selection is upstream; this checks its output against the
narration, source timecodes and ORIGINAL claim IDs. It is not a truth oracle.
"""
from __future__ import annotations
import math
from .evidence import _SHA

def _time(value):
    return (type(value) in (int,float) and math.isfinite(value))

def bind_sentences_to_shots(*,source_sha256:str,source_duration_s:float,
       voice_duration_s:float,catalog:dict,sentences:list[dict],
       voice_timeline:list[dict],chosen:dict[str,str])->dict:
    if not _SHA.fullmatch(str(source_sha256)):
        raise ValueError("Invalid source sha")
    if not _time(source_duration_s) or source_duration_s<=0:
        raise ValueError("Invalid original duration")
    if not _time(voice_duration_s) or voice_duration_s<=0:
        raise ValueError("Invalid real narration duration")
    if not isinstance(sentences,list) or not sentences or not isinstance(catalog,dict):
        raise ValueError("Missing source-backed review")
    if not isinstance(voice_timeline,list) or not isinstance(chosen,dict):
        raise ValueError("Missing real narration/shot selection")
    timelines={}
    for row in voice_timeline:
        if not isinstance(row,dict):
            raise ValueError("Invalid sentence timeline")
        sid=row.get("sentence_id")
        start,end=row.get("voice_start_s"),row.get("voice_end_s")
        if (not isinstance(sid,str) or sid in timelines or
            not _time(start) or not _time(end) or not 0<=start<end<=voice_duration_s+0.045):
            raise ValueError("Invalid voice time or duplicate sentence")
        timelines[sid]={"start":start,"end":end}
    ids=[x.get("sentence_id") for x in sentences]
    if (len(set(ids))!=len(ids) or set(ids)!=set(timelines) or
        set(ids)!=set(chosen)):
        raise ValueError("Narration/claim/shot sentence ID mismatch")
    output=[]
    previous_end=-1.
    for item in sentences:
        sid=item["sentence_id"]
        clock=timelines[sid]
        if clock["start"]<previous_end-0.045:
            raise ValueError("Narration sentences overlap")
        previous_end=clock["end"]
        eid=chosen[sid]
        evidence=catalog.get(eid)
        if not isinstance(evidence,dict) or evidence.get("source_sha256")!=source_sha256:
            raise ValueError("Missing source-matched chosen evidence")
        a,b=evidence.get("start_s"),evidence.get("end_s")
        if not _time(a) or not _time(b) or not 0<=a<b<=source_duration_s+0.001:
            raise ValueError("Chosen source evidence time invalid")
        claims=item.get("atomic_claims")
        if not isinstance(claims,list) or not claims:
            raise ValueError("Missing atomic claims")
        verdict=None
        for claim in claims:
            if not isinstance(claim,dict) or claim.get("source_sha256")!=source_sha256:
                raise ValueError("Claim source provenance changed")
            v=claim.get("verdict")
            allowed={"VISUAL_DIRECT":"visual","DIALOGUE_SUPPORTED":"asr"}
            if v not in allowed:
                raise ValueError("Unresolved/contradicted claim cannot be rendered")
            if evidence.get("kind")!=allowed[v] or eid not in claim.get("evidence_ids",[]):
                raise ValueError("Chosen scene evidence does not match N05 claim")
            if claim.get("text")!=evidence.get("text"):
                raise ValueError("Claim wording differs from literal source evidence")
            if verdict is not None and verdict!=v:
                raise ValueError("One shot cannot support mixed claim modalities")
            verdict=v
        output.append({"sentence_id":sid,"review_text":item["review_text"],
          "voice_start_s":clock["start"],"voice_end_s":clock["end"],
          "atomic_claims":claims,"unresolved_claims":[],
          "chosen_shots":[{
            "source_start_s":a,"source_end_s":b,
            "voice_start_s":clock["start"],"voice_end_s":clock["end"],
            "visual_evidence_ids":[eid] if verdict=="VISUAL_DIRECT" else [],
            "asr_evidence_ids":[eid] if verdict=="DIALOGUE_SUPPORTED" else [],
            "verdict":verdict,
            "qualifier":"Evidence-linked source quote; semantic correctness still needs human review"}]})
    return {"source_movie_sha256":source_sha256,
            "source_duration_s":source_duration_s,
            "narration_duration_s":voice_duration_s,
            "sentences":output,
            "human_review_required":True,
            "semantic_truth_certified":False}
