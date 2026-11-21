"""Ordered source-frame observations with explicit unverified motion hypotheses."""
from __future__ import annotations
import math
from .translation import HEX64,EVIDENCE_ID

def build_temporal_pack(source_sha256:str,source_duration_s:float,
                        frames:list[dict],model_caption:str)->dict:
    if not isinstance(source_sha256,str) or not HEX64.fullmatch(source_sha256):
        raise ValueError("Invalid source movie SHA")
    if type(source_duration_s) not in (int,float) or not math.isfinite(source_duration_s) or source_duration_s<=0:
        raise ValueError("Invalid source duration")
    if not isinstance(frames,list) or len(frames)<2:
        raise ValueError("At least two film frames required for temporal hypothesis")
    if len(frames)>64:
        raise ValueError("Excessive temporal frame window")
    if not isinstance(model_caption,str) or not model_caption.strip() or len(model_caption)>2500:
        raise ValueError("Missing temporal model caption")
    last=-1.
    seen=set()
    ids=[]
    times=[]
    for frame in frames:
        if not isinstance(frame,dict):
            raise ValueError("Malformed source frame")
        id=frame.get("id")
        if not isinstance(id,str) or not EVIDENCE_ID.fullmatch(id) or id in seen:
            raise ValueError("Duplicate or invalid frame id")
        if frame.get("source_sha256")!=source_sha256:
            raise ValueError("Frame source SHA mismatch")
        h=frame.get("frame_sha256")
        if not isinstance(h,str) or not HEX64.fullmatch(h):
            raise ValueError("Frame SHA missing")
        t=frame.get("frame_center_s")
        if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=source_duration_s:
            raise ValueError("Frame time out of source")
        if t<=last:
            raise ValueError("Source frames must be in strict time order")
        last=t
        seen.add(id);ids.append(id);times.append(float(t))
    return {"schema_version":"5.0","source_sha256":source_sha256,
            "frame_ids":ids,"frame_times_s":times,
            "source_window_s":[times[0],times[-1]],
            "ordered_caption":model_caption.strip(),
            "temporal_statement_status":"MODEL_HYPOTHESIS_NEEDS_HUMAN_VIDEO_REVIEW",
            "action_certified":False,"characters_certified":False,
            "human_video_review_completed":False,
            "limitations":["Discrete frames are not continuous action video",
                           "Temporal vision hallucinations are possible",
                           "No independent confirmation of identities, gunfire or causality"]}
