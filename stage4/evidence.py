"""Evidence-bound N04 story event compiler.

Does NOT infer plot, identity, motives, ownership or off-screen events.
Source evidence must be independently model/human verified by its producer.
"""
from __future__ import annotations
import math
import re

_SHA=re.compile(r"^[0-9a-f]{64}$")
def _span(row:dict,duration:float)->tuple[float,float]:
    a,b=row.get("start_s"),row.get("end_s")
    if (isinstance(a,bool) or isinstance(b,bool) or
        not isinstance(a,(int,float)) or not isinstance(b,(int,float)) or
        not math.isfinite(a) or not math.isfinite(b) or
        a<0 or a>=b or b>duration+0.001):
        raise ValueError("evidence time out of source bounds")
    return float(a),float(b)

def _overlap(a,b)->float:
    return max(0.0,min(a[1],b[1])-max(a[0],b[0]))

def build_timeline(asr_rows:list[dict],visual_rows:list[dict],
                   source_sha256:str,source_duration_s:float)->dict:
    if not _SHA.fullmatch(str(source_sha256)):
        raise ValueError("invalid source SHA")
    if (not isinstance(source_duration_s,(int,float)) or
        isinstance(source_duration_s,bool) or
        not math.isfinite(source_duration_s) or source_duration_s<=0):
        raise ValueError("invalid source duration")
    if not isinstance(asr_rows,list) or not isinstance(visual_rows,list):
        raise ValueError("source evidence must be lists")
    if not asr_rows and not visual_rows:
        raise ValueError("empty evidence collection")
    catalog={}
    for kind,rows,field in (("visual",visual_rows,"description"),("asr",asr_rows,"text")):
        for row in rows:
            if not isinstance(row,dict):
                raise ValueError("invalid source evidence row")
            rid=row.get("id")
            if not isinstance(rid,str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",rid):
                raise ValueError("invalid evidence id")
            if rid in catalog:
                raise ValueError("duplicate evidence id: "+rid)
            if row.get("source_sha256")!=source_sha256:
                raise ValueError("evidence source SHA does not match movie")
            text=row.get(field)
            if not isinstance(text,str) or not text.strip() or len(text)>4000:
                raise ValueError("invalid evidence text")
            a,b=_span(row,source_duration_s)
            catalog[rid]={"kind":kind,"text":text.strip(),"start_s":a,"end_s":b,
                          "source_sha256":source_sha256}

    visuals=sorted((r for r in catalog.items() if r[1]["kind"]=="visual"),
                   key=lambda pair:(pair[1]["start_s"],pair[1]["end_s"],pair[0]))
    asrs=sorted((r for r in catalog.items() if r[1]["kind"]=="asr"),
                key=lambda pair:(pair[1]["start_s"],pair[0]))
    # Group *identical* visual intervals, never invent a cut at an ASR boundary.
    groups=[]
    for rid,row in visuals:
        if groups and groups[-1]["bounds"]==(row["start_s"],row["end_s"]):
            groups[-1]["visual_evidence_ids"].append(rid)
        else:
            groups.append({"bounds":(row["start_s"],row["end_s"]),
                           "visual_evidence_ids":[rid],"asr_evidence_ids":[]})
    for rid,row in asrs:
        aspan=(row["start_s"],row["end_s"])
        candidates=[(_overlap(aspan,g["bounds"]),idx)
                    for idx,g in enumerate(groups)]
        candidates=[(overlap,idx) for overlap,idx in candidates if overlap>0.0001]
        if candidates:
            _,idx=max(candidates,key=lambda x:(x[0],-x[1]))
            groups[idx]["asr_evidence_ids"].append(rid)
        else:
            groups.append({"bounds":aspan,"visual_evidence_ids":[],
                           "asr_evidence_ids":[rid]})
    groups.sort(key=lambda g:(g["bounds"][0],g["bounds"][1]))
    events=[]
    unresolved=[]
    for index,g in enumerate(groups,1):
        vis=g["visual_evidence_ids"]
        descriptions={catalog[x]["text"].casefold().strip() for x in vis}
        conflict=len(descriptions)>1
        # Overlapping spans with different captions also require human reconciliation.
        if vis:
            for other in groups:
                if other is g or not other["visual_evidence_ids"]:continue
                overlap=_overlap(g["bounds"],other["bounds"])
                dur=min(g["bounds"][1]-g["bounds"][0],
                        other["bounds"][1]-other["bounds"][0])
                if overlap>0.25*dur and any(
                    catalog[x]["text"].casefold().strip()!=catalog[y]["text"].casefold().strip()
                    for x in vis for y in other["visual_evidence_ids"]):
                    conflict=True
        event_id=f"EVT{index:04d}"
        if conflict:
            unresolved.append({"event_id":event_id,"reason":"conflicting_visual_observations",
                               "evidence_ids":vis[:]})
        events.append({
            "event_id":event_id,"start_s":g["bounds"][0],"end_s":g["bounds"][1],
            "source_sha256":source_sha256,
            "visual_evidence_ids":vis[:],
            "asr_evidence_ids":g["asr_evidence_ids"][:],
            "visual_description":catalog[vis[0]]["text"] if vis and not conflict else None,
            "spoken_text":" ".join(catalog[x]["text"] for x in g["asr_evidence_ids"]),
            "visual_conflict":conflict,
            "human_review_required":True})
    return {"schema_version":"4.0","source_sha256":source_sha256,
            "source_duration_s":float(source_duration_s),"catalog":catalog,
            "events":events,"unresolved":unresolved,
            "model_semantic_truth_verified":False,"human_approval_required":True}
