"""Construct unsigned requests for a SEPARATE trusted human-approval service.

These requests are not approval receipts. Do not store a signer or signing key
inside agent-controlled code or output. Engine21 gates always verify signatures.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/"skills"/"film-review-orchestrator"/"scripts"))
from engine21 import state,gates

GATES=("script","voice","pilot")

def make_request(job:Path,gate:str)->dict:
    job=Path(job).resolve(strict=True)
    if gate not in GATES:
        raise ValueError("Invalid human approval gate")
    details=state.job_details(job)
    s=state.read_state(job)
    if s.get("job_id")!=details.get("job_id"):
        raise ValueError("Engine job_id mismatch")
    if s.get("source_sha256")!=details["source"]["sha256"] or not state.source_valid(job):
        raise ValueError("Original source SHA changed")
    if gate=="script":
        stage=s["stages"]["N05"]
        if stage.get("status")!="DONE":
            raise ValueError("N05 review not completed")
        evidence=stage.get("evidence_path")
        digest=stage.get("evidence_sha256")
        if not evidence or not digest or state.sha256(state.inside_job(job,evidence))!=digest:
            raise ValueError("N05 evidence SHA mismatch")
        scripts=[x for x in stage.get("artifacts",[])
                 if Path(x.get("path","")).name=="review_final.txt"]
        if len(scripts)!=1:
            raise ValueError("N05 review text artifact missing")
        review_path=state.inside_job(job,scripts[0]["path"])
        if state.sha256(review_path)!=scripts[0].get("sha256"):
            raise ValueError("N05 review SHA mismatch")
        script_hash=state.sha256(review_path)
    else:
        script_hash=None
    # Engine21 computes these exact subjects again when checking signed receipts.
    subject=gates._subject(job,s,gate)
    core={"schema_version":"4.0","job_id":s["job_id"],"gate":gate,
          "source_sha256":s["source_sha256"],"subject_sha256":subject,
          "status":"PENDING_HUMAN_DECISION","unsigned":True,
          "human_approved":False,
          "review_text_sha256":script_hash,
          "subject_semantics":{
             "script":"N05 evidence.json SHA; Engine21 reviews content of N05 evidence",
             "voice":"voice/approved_sample.wav SHA (full audio decode required)",
             "pilot":"edit/pilot.mp4 SHA (full audio/video decode required)"
          }[gate],
          "warnings":["Only an actual human review via trusted host can create a signed receipt",
                      "Never accept this request JSON as an approval receipt",
                      "Model agent must not access signing keys"]}
    core["request_id"]=hashlib.sha256(json.dumps(
        {"job_id":core["job_id"],"gate":gate,"subject_sha256":subject},
        sort_keys=True).encode("utf8")).hexdigest()[:24]
    return core

def save_request(job:Path,request:dict)->Path:
    job=Path(job).resolve(strict=True)
    if not isinstance(request,dict) or request.get("gate") not in GATES:
        raise ValueError("Invalid request")
    if "signature" in request or request.get("human_approved") is not False:
        raise ValueError("Refusing request that claims human approval")
    current=make_request(job,request["gate"])
    if request!=current:
        raise ValueError("Request subject stale or contents modified")
    destdir=job/"approvals"/"requests"
    if destdir.is_symlink() or (job/"approvals").is_symlink():
        raise ValueError("Approval requests path must not be symlink")
    destdir.mkdir(parents=True,exist_ok=True)
    dest=destdir/(request["gate"]+"-"+request["request_id"]+".request.json")
    if dest.exists():
        raise FileExistsError("Existing request must never be overwritten")
    with dest.open("x",encoding="utf8") as f:
        f.write(json.dumps(request,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    return dest
