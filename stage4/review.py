"""Grounded extractive review drafts.

No candidate narrative beyond exact source statements is automatically asserted.
Unverified model output is QUARANTINED for host/human review, not passed to TTS.
"""
from __future__ import annotations
import math
from .evidence import _SHA

def _supported_proposal(proposal:dict, events:dict,catalog:dict):
    if not isinstance(proposal,dict):
        return False,"malformed proposal"
    event=events.get(proposal.get("event_id"))
    if event is None:
        return False,"unknown source event"
    text=proposal.get("review_text")
    claim=proposal.get("claim_text")
    ids=proposal.get("evidence_ids")
    verdict=proposal.get("verdict")
    if not isinstance(text,str) or not text.strip() or len(text)>4000:
        return False,"invalid proposed review sentence"
    if not isinstance(claim,str) or not claim.strip():
        return False,"invalid proposed claim"
    if not isinstance(ids,list) or not ids or any(not isinstance(i,str) for i in ids):
        return False,"missing source evidence"
    allowed=(set(event["visual_evidence_ids"]) if verdict=="VISUAL_DIRECT"
             else set(event["asr_evidence_ids"]) if verdict=="DIALOGUE_SUPPORTED"
             else set())
    if not allowed or not set(ids)<=allowed:
        return False,"unknown or incompatible evidence reference"
    if verdict=="VISUAL_DIRECT" and event.get("visual_conflict"):
        return False,"conflicting visual observations"
    if not any(claim.strip()==catalog[id]["text"] for id in ids):
        return False,"claim differs from literal source statement"
    valid_text=(claim.strip(),f"Hình ảnh ghi nhận: {claim.strip()}",
                f"Lời thoại ghi nhận: “{claim.strip()}”")
    if text.strip() not in valid_text:
        return False,"proposed sentence adds unsupported content"
    return True,""

def build_review(timeline:dict,proposals:list[dict]|None=None,
                 max_sentences:int|None=None)->dict:
    if not isinstance(timeline,dict) or timeline.get("schema_version")!="4.0":
        raise ValueError("Invalid source timeline")
    source=timeline.get("source_sha256")
    if not _SHA.fullmatch(str(source)):
        raise ValueError("Invalid source SHA")
    catalog=timeline.get("catalog")
    events=timeline.get("events")
    if not isinstance(catalog,dict) or not isinstance(events,list) or not events:
        raise ValueError("No grounded event source")
    if max_sentences is not None and (type(max_sentences) is not int or max_sentences<1):
        raise ValueError("max_sentences must be positive")
    if proposals is not None and not isinstance(proposals,list):
        raise ValueError("Proposals must be list")
    records=[]
    quarantine=[]
    ledger=[]
    event_index={}
    for event in events:
        eid=event.get("event_id")
        if not isinstance(eid,str) or eid in event_index:
            raise ValueError("Invalid or duplicate event")
        if event.get("source_sha256")!=source:
            raise ValueError("Event source SHA differs")
        event_index[eid]=event
        items=[]
        if not event.get("visual_conflict"):
            for vid in event.get("visual_evidence_ids",[]):
                if vid not in catalog or catalog[vid]["kind"]!="visual":
                    raise ValueError("Unknown event visual evidence")
                items.append(("VISUAL_DIRECT",vid,"Hình ảnh ghi nhận: "+catalog[vid]["text"]))
        for aid in event.get("asr_evidence_ids",[]):
            if aid not in catalog or catalog[aid]["kind"]!="asr":
                raise ValueError("Unknown event dialogue evidence")
            items.append(("DIALOGUE_SUPPORTED",aid,"Lời thoại ghi nhận: “"+catalog[aid]["text"]+"”"))
        for verdict,rid,review in items:
            evidence=catalog[rid]
            if evidence["source_sha256"]!=source:
                raise ValueError("Evidence source SHA differs")
            records.append({"event_id":eid,"review_text":review,
                            "kind":verdict,"evidence_ids":[rid],
                            "source_start_s":evidence["start_s"],
                            "source_end_s":evidence["end_s"],
                            "claim_text":evidence["text"]})
    for proposal in proposals or []:
        supported,reason=_supported_proposal(proposal,event_index,catalog)
        if not supported:
            quarantine.append({"proposal":proposal,"reason":reason,
                               "status":"UNRESOLVED_REQUIRES_HUMAN_REVIEW"})
            continue
        rid=proposal["evidence_ids"][0]
        evidence=catalog[rid]
        records.append({"event_id":proposal["event_id"],
                        "review_text":proposal["review_text"].strip(),
                        "kind":proposal["verdict"],
                        "evidence_ids":proposal["evidence_ids"][:],
                        "source_start_s":evidence["start_s"],
                        "source_end_s":evidence["end_s"],
                        "claim_text":proposal["claim_text"].strip()})
    if not records:
        raise ValueError("No grounded review text; all source claims unresolved")
    full_count=len(records)
    if max_sentences is not None:
        records=records[:max_sentences]
    sentences=[]
    for index,row in enumerate(records,1):
        sid=f"S{index:04d}"
        cid=f"C{index:04d}"
        claim={"claim_id":cid,"text":row["claim_text"],
               "verdict":row["kind"],"evidence_ids":row["evidence_ids"],
               "source_sha256":source}
        sentences.append({"sentence_id":sid,"event_id":row["event_id"],
                          "review_text":row["review_text"],
                          "source_sha256":source,
                          "source_start_s":row["source_start_s"],
                          "source_end_s":row["source_end_s"],
                          "atomic_claims":[claim],
                          "human_review_required":True})
        ledger.append({"sentence_id":sid,"claim_id":cid,
                       "verdict":claim["verdict"],
                       "evidence_ids":claim["evidence_ids"],
                       "source_sha256":source,
                       "source_start_s":row["source_start_s"],
                       "source_end_s":row["source_end_s"],
                       "manual_review_required":True})
    return {"schema_version":"4.0","source_sha256":source,
            "review_text":"\n".join(s["review_text"] for s in sentences),
            "sentences":sentences,"evidence_ledger":ledger,
            "quarantined_proposals":quarantine,"truncated":len(records)<full_count,
            "human_approval_required":True,"approved_for_publication":False,
            "narrative_truth_verified":False,
            "limitations":["Extractive source quotes, not autonomous plot interpretation",
                           "Source model descriptions may still be incorrect",
                           "External human review and Engine21 script gate required"]}
