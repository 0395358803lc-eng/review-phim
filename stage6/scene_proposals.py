"""FFmpeg scene-boundary proposals mapped back to full movie timecodes.

Scene scores are cut proposals, never proof of character actions or plot.
"""
from __future__ import annotations
import math
from stage5.translation import HEX64,EVIDENCE_ID

def valid_num(v):return type(v) in (int,float) and math.isfinite(v)

def build_scene_proposals(source_sha256:str,movie_duration_s:float,
                          windows:list[dict],cuts_by_window:dict)->dict:
    if not isinstance(source_sha256,str) or not HEX64.fullmatch(source_sha256):
        raise ValueError("Original movie source SHA invalid")
    if not valid_num(movie_duration_s) or movie_duration_s<=0:
        raise ValueError("Invalid source duration")
    if not isinstance(windows,list) or not windows or not isinstance(cuts_by_window,dict):
        raise ValueError("Missing original windows or sample cuts")
    seen=set()
    registered=[]
    for w in windows:
        if not isinstance(w,dict):raise ValueError("Malformed window")
        id=w.get("sample_id")
        if not isinstance(id,str) or not EVIDENCE_ID.fullmatch(id) or id in seen:
            raise ValueError("Duplicate or invalid sample id")
        beg,end=w.get("original_start_s"),w.get("original_end_s")
        if not valid_num(beg) or not valid_num(end) or not 0<=beg<end<=movie_duration_s+.001:
            raise ValueError("Source window outside original film")
        registered.append((id,float(beg),float(end)))
        seen.add(id)
    registered.sort(key=lambda item:item[1])
    for prev,next_ in zip(registered,registered[1:]):
        if next_[1]<prev[2]-.0001:raise ValueError("Authorized source windows overlap")
    if set(cuts_by_window)!=seen:
        raise ValueError("Scene cut sample keys differ from source sample IDs")
    proposed=[]
    for id,beg,end in registered:
        relative=cuts_by_window[id]
        if not isinstance(relative,list):raise ValueError("Invalid scene cut list")
        duration=end-beg
        last=0.
        for cut in relative:
            if not valid_num(cut) or not .0001<cut<duration-.0001:
                raise ValueError("Scene cut outside sampled window")
            if cut-last<.08:
                raise ValueError("Scene cuts duplicated/unordered/too close")
            last=float(cut)
        points=[0.,*[float(x) for x in relative],duration]
        for idx,(a,b) in enumerate(zip(points,points[1:]),1):
            if b-a<.08:
                raise ValueError("Scene cut makes invalid tiny shot interval")
            proposed.append({"scene_id":f"SHOT_{id}_{idx:03d}",
                "source_sha256":source_sha256,
                "source_sample_id":id,
                "source_interval_s":[round(beg+a,3),round(beg+b,3)],
                "relative_sample_interval_s":[round(a,3),round(b,3)],
                "status":"AUTO_SCENE_CANDIDATE_PENDING_VIDEO_REVIEW",
                "human_review_required":True,
                "real_action_verified":False,
                "boundary_detection_method":"ffmpeg_scene_score_candidate"})
    if len({x["scene_id"] for x in proposed})!=len(proposed):
        raise ValueError("Duplicate scene IDs")
    return {"schema_version":"6.0","source_sha256":source_sha256,
            "movie_duration_s":float(movie_duration_s),
            "sample_count":len(registered),
            "scenes":proposed,"auto_detected_cuts":sum(len(x) for x in cuts_by_window.values()),
            "real_movie_actions_certified":False,
            "human_continuous_video_review_required":True,
            "can_render":False,
            "limitations":["FFmpeg scene cut scores are proposals not narrative boundaries",
                          "Only existing authorized excerpts scanned, not full movie"]}
