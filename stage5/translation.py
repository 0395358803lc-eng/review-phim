"""Source-locked English-to-Vietnamese candidates, never a truth/approval oracle."""
from __future__ import annotations
import hashlib
import math
import re

HEX64=re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_ID=re.compile(r"^[A-Za-z0-9_-]{1,64}$")

def text_sha(text:str)->str:
    return hashlib.sha256(text.encode("utf8")).hexdigest()

def build_translation_pack(asr_rows:list[dict],source_sha256:str,
                           source_duration_s:float,
                           proposals:list[dict]|None=None)->dict:
    if not isinstance(source_sha256,str) or not HEX64.fullmatch(source_sha256):
        raise ValueError("invalid original source SHA")
    if (type(source_duration_s) not in (float,int)
          or not math.isfinite(source_duration_s) or source_duration_s<=0):
        raise ValueError("invalid source duration")
    if not isinstance(asr_rows,list) or not asr_rows:
        raise ValueError("empty English ASR source")
    if proposals is not None and not isinstance(proposals,list):
        raise ValueError("translation proposals must be a list")
    rows=[]
    index={}
    for row in asr_rows:
        if not isinstance(row,dict):
            raise ValueError("ASR record must be object")
        id=row.get("id")
        if not isinstance(id,str) or not EVIDENCE_ID.fullmatch(id):
            raise ValueError("Invalid ASR id")
        if id in index:
            raise ValueError("duplicate ASR id "+id)
        if row.get("source_sha256")!=source_sha256:
            raise ValueError("ASR source movie SHA mismatch")
        lang=row.get("original_spoken_language",row.get("language","en"))
        if lang!="en":
            raise ValueError("source is not annotated as English")
        start,end=row.get("start_s"),row.get("end_s")
        if (type(start) not in (int,float) or type(end) not in (int,float)
            or not math.isfinite(start) or not math.isfinite(end)
            or not 0<=start<end<=source_duration_s+0.001):
            raise ValueError("English ASR time out of source bounds")
        original=row.get("text")
        if not isinstance(original,str) or not original.strip() or len(original)>6000:
            raise ValueError("English ASR text absent")
        logprob=row.get("avg_logprob")
        if logprob is not None and (type(logprob) not in (int,float) or not math.isfinite(logprob)):
            raise ValueError("Invalid ASR confidence value")
        status=("NEEDS_AUDIO_LISTENING" if logprob is None or logprob<=-0.35
                else "UNVERIFIED_ASR")
        item={"id":id,"start_s":float(start),"end_s":float(end),
              "source_sha256":source_sha256,
              "original_english":original,
              "original_text_sha256":text_sha(original),
              "language_original":"en","avg_logprob":logprob,
              "asr_risk":status,
              "translation_vi_candidate":None,
              "translation_model_id":None,
              "human_approved":False,
              "status":"AWAITING_VIETNAMESE_TRANSLATION"}
        rows.append(item)
        index[id]=item
    quarantined=[]
    groups={}
    for p in proposals or []:
        if not isinstance(p,dict):
            quarantined.append({"reason":"malformed_translation_proposal"})
            continue
        ident=p.get("evidence_id")
        if not isinstance(ident,str) or not EVIDENCE_ID.fullmatch(ident):
            quarantined.append({"reason":"invalid_ASR_id"})
            continue
        groups.setdefault(ident,[]).append(p)
    for ident,proposals_group in groups.items():
        item=index.get(ident)
        if item is None:
            quarantined.extend({"evidence_id":ident,"reason":"unknown_ASR_id"} for _ in proposals_group)
            continue
        if len(proposals_group)>1:
            quarantined.extend({"evidence_id":ident,"reason":"duplicate_translations_ambiguous"} for _ in proposals_group)
            continue
        p=proposals_group[0]
        vi=p.get("translation_vi")
        model=p.get("model_id")
        if p.get("human_approved") is not False:
            reason="model_may_not_claim_approval"
        elif p.get("english_text_sha256")!=item["original_text_sha256"]:
            reason="original_english_text_SHA_mismatch"
        elif not isinstance(vi,str) or not vi.strip() or len(vi)>6000:
            reason="invalid_vietnamese_translation"
        elif not isinstance(model,str) or not model.strip() or len(model)>128:
            reason="translation_model_provenance_missing"
        else:
            reason=None
        if reason:
            quarantined.append({"evidence_id":ident,"reason":reason})
            continue
        item["translation_vi_candidate"]=vi.strip()
        item["translation_model_id"]=model
        item["status"]="TRANSLATION_PENDING_HUMAN_REVIEW"
    return {"schema_version":"5.0","movie_source_sha256":source_sha256,
            "source_duration_s":float(source_duration_s),
            "rows":rows,"quarantined":quarantined,
            "source_english_preserved":True,
            "translation_semantics_certified":False,
            "voice_or_pilot_approved":False,
            "warning":"Machine translations require listening and independent human review before use as film dialogue"}
