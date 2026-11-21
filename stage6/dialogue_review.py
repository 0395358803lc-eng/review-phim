"""PENDING human listening queue, source-locked to unedited English ASR."""
from __future__ import annotations
import math
import re
from stage5.translation import HEX64,EVIDENCE_ID,text_sha

def _finite(x):
    return type(x) in (float,int) and math.isfinite(x)

def _windows(windows,source_duration_s):
    if not isinstance(windows,list) or not windows:
        raise ValueError("Missing authorized source sample windows")
    normalized=[]
    seen=set()
    for w in windows:
        if not isinstance(w,dict):raise ValueError("Malformed sample window")
        id=w.get("sample_id")
        start,end=w.get("original_start_s"),w.get("original_end_s")
        if not isinstance(id,str) or not EVIDENCE_ID.fullmatch(id) or id in seen:
            raise ValueError("Invalid or duplicate source window")
        if not _finite(start) or not _finite(end) or not 0<=start<end<=source_duration_s+0.001:
            raise ValueError("Invalid authorized source window bounds")
        seen.add(id)
        normalized.append({"sample_id":id,"original_start_s":float(start),"original_end_s":float(end)})
    normalized.sort(key=lambda x:x["original_start_s"])
    for last,now in zip(normalized,normalized[1:]):
        if now["original_start_s"]<last["original_end_s"]-0.0001:
            raise ValueError("Source sample windows overlap")
    return normalized

def build_dialogue_review_queue(translation_pack:dict,original_asr_rows:list[dict],
                 source_sha256:str,movie_duration_s:float,source_windows:list[dict])->dict:
    if not isinstance(source_sha256,str) or not HEX64.fullmatch(source_sha256):
        raise ValueError("Movie source SHA invalid")
    if not _finite(movie_duration_s) or movie_duration_s<=0:
        raise ValueError("Movie duration invalid")
    if not isinstance(translation_pack,dict) or translation_pack.get("movie_source_sha256")!=source_sha256:
        raise ValueError("Translation source movie SHA changed")
    if translation_pack.get("translation_semantics_certified") is not False:
        raise ValueError("Untrusted translation approval flag")
    windows=_windows(source_windows,movie_duration_s)
    if not isinstance(original_asr_rows,list) or not original_asr_rows:
        raise ValueError("Missing original English ASR rows")
    if not isinstance(translation_pack.get("rows"),list):
        raise ValueError("Missing Stage5 translation ASR rows")
    originals={}
    for raw in original_asr_rows:
        if not isinstance(raw,dict):raise ValueError("Malformed original ASR")
        rid=raw.get("id")
        if not isinstance(rid,str) or not EVIDENCE_ID.fullmatch(rid):
            raise ValueError("Invalid original ASR ID")
        if rid in originals:raise ValueError("duplicate original ASR ID")
        if raw.get("source_sha256")!=source_sha256:
            raise ValueError("Original ASR source SHA differs")
        if raw.get("original_spoken_language",raw.get("language","en"))!="en":
            raise ValueError("Expected unmodified English source language")
        text=raw.get("text")
        if not isinstance(text,str) or not text.strip():
            raise ValueError("Empty original English ASR")
        a,b=raw.get("start_s"),raw.get("end_s")
        if not _finite(a) or not _finite(b) or not 0<=a<b<=movie_duration_s+.001:
            raise ValueError("Original ASR time invalid")
        originals[rid]=raw
    rows=[]
    ids=set()
    for draft in translation_pack["rows"]:
        if not isinstance(draft,dict):raise ValueError("Malformed translated ASR row")
        rid=draft.get("id")
        if not isinstance(rid,str) or not EVIDENCE_ID.fullmatch(rid):
            raise ValueError("Invalid translated ASR ID")
        if rid in ids:raise ValueError("duplicate translated ASR row")
        ids.add(rid)
        source=originals.get(rid)
        if source is None:raise ValueError("ASR translation has unknown source ID")
        if draft.get("source_sha256")!=source_sha256:
            raise ValueError("Translation row source SHA changed")
        en=source["text"]
        if (draft.get("original_english")!=en or
            draft.get("original_text_sha256")!=text_sha(en)):
            raise ValueError("English transcript text/hash mismatch")
        start,end=source["start_s"],source["end_s"]
        if (not _finite(draft.get("start_s")) or not _finite(draft.get("end_s")) or
            abs(draft["start_s"]-start)>.001 or abs(draft["end_s"]-end)>.001):
            raise ValueError("Translated ASR time shifted away from original audio")
        if draft.get("human_approved") not in (False,None):
            raise ValueError("No genuine approval of machine translation supplied")
        match=[w for w in windows if start>=w["original_start_s"]-.001 and
               end<=w["original_end_s"]+.001]
        if len(match)!=1:
            raise ValueError("Original ASR interval falls outside authorized source window")
        w=match[0]
        vi=draft.get("translation_vi_candidate")
        if vi is not None and (not isinstance(vi,str) or not vi.strip()):
            raise ValueError("Invalid Vietnamese translation candidate")
        prob=source.get("avg_logprob")
        if prob is not None and not _finite(prob):
            raise ValueError("Invalid original ASR likelihood")
        flags=[]
        if prob is None or prob<=-.35:flags.append("LOW_ASR_CONFIDENCE_LISTEN")
        if vi is None:flags.append("MISSING_TRANSLATION")
        elif re.search(r"(?i)\bletters?\s+(?:to|for)\s+(?:santa|santa claus)\b",en) and "chữ cái" in vi.casefold():
            flags.append("MAIL_LETTERS_FALSE_FRIEND")
        priority=("CHECK_AUDIO_FIRST" if "LOW_ASR_CONFIDENCE_LISTEN" in flags
                  else "CHECK_TRANSLATION_MEANING" if "MAIL_LETTERS_FALSE_FRIEND" in flags
                  else "NORMAL_HUMAN_REVIEW")
        rows.append({"id":rid,"original_english":en,
             "original_text_sha256":text_sha(en),"source_sha256":source_sha256,
             "translation_vi_candidate":vi,
             "source_sample_id":w["sample_id"],"start_s":float(start),"end_s":float(end),
             "preview_start_s":round(max(w["original_start_s"],start-.5),3),
             "preview_end_s":round(min(w["original_end_s"],end+.5),3),
             "source_window_s":[w["original_start_s"],w["original_end_s"]],
             "asr_avg_logprob":prob,"risk_flags":flags,"priority":priority,
             "review_status":"PENDING_HUMAN_LISTEN",
             "transcript_confirmed":False,"translation_confirmed":False,
             "reviewer":None,"review_notes":None,
             "eligible_for_review_voice":False})
    if ids!=set(originals):
        raise ValueError("ASR source/translation row IDs incomplete")
    rows.sort(key=lambda x:(x["start_s"],x["id"]))
    return {"schema_version":"6.0","source_sha256":source_sha256,
            "movie_duration_s":movie_duration_s,
            "rows":rows,"source_windows":windows,
            "pending_count":len(rows),
            "low_asr_count":sum("LOW_ASR_CONFIDENCE_LISTEN" in r["risk_flags"] for r in rows),
            "translation_warning_count":sum("MAIL_LETTERS_FALSE_FRIEND" in r["risk_flags"] for r in rows),
            "script_or_voice_approved":False,
            "all_dialogue_verified_by_human":False,
            "limitations":["Model-transcribed English, human has not listened to originals",
                "Translations are machine proposals, not endorsed dialogue",
                "Preview clips limited to previous user-authorized film excerpts"]}
