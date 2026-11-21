#!/usr/bin/env python3
"""Standalone, synthetic Windows acceptance of Engine 2.1, with real FFmpeg/CLI.

No film assets, no real human approvals, no installation, no Git writes.
Run only in an explicitly authorized isolated __ENGINE21_QA_* directory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "skills/film-review-orchestrator/scripts"))
import jobctl
from engine21 import state

ADAPTER = r'''import json,hashlib,os,shutil,subprocess
from pathlib import Path
out=Path(os.environ["FRA_OUTPUT_DIR"])
src=Path(os.environ["FRA_SOURCE"])
stage=os.environ["FRA_STAGE"]
job=Path(os.environ["FRA_JOB"])
artifacts=[]
for name in json.loads(os.environ["FRA_REQUIRED_OUTPUTS"]):
    p=out/name
    if name.endswith(".mp4"):
        shutil.copy2(src,p)
    elif name.endswith(".wav"):
        subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi","-i",
                        "sine=frequency=440:duration=0.6","-y",str(p)],
                       check=True,timeout=20)
    elif name=="source_manifest.json":
        p.write_text(json.dumps({"source_sha256":os.environ["FRA_SOURCE_SHA256"]}))
    elif name=="sentence_shot_map.json":
        doc={"source_movie_sha256":os.environ["FRA_SOURCE_SHA256"],
          "source_duration_s":1.2,"narration_duration_s":0.6,
          "sentences":[{"sentence_id":"S0001","review_text":"SYNTHETIC TEST ONLY",
            "voice_start_s":0,"voice_end_s":0.6,
            "atomic_claims":[{"claim_id":"C0001","text":"fixture",
              "verdict":"CONTEXT_ONLY","evidence_ids":[]}],
            "chosen_shots":[{"source_start_s":0.1,"source_end_s":0.7,
              "voice_start_s":0,"voice_end_s":0.6,
              "visual_evidence_ids":[],"asr_evidence_ids":[],
              "verdict":"CONTEXT_ONLY","qualifier":"Synthetic fixture only"}],
            "unresolved_claims":[]}]}
        p.write_text(json.dumps(doc))
    elif name.endswith(".jsonl"):
        p.write_text(json.dumps({"fixture":True,"stage":stage})+"\n")
    elif name.endswith(".json"):
        p.write_text(json.dumps({"fixture":True,"stage":stage}))
    else:
        p.write_text("Synthetic QA only\n")
    artifacts.append({"path":str(p.relative_to(job)),
                      "sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
doc={"stage":stage,"outcome":"PASS",
 "source_sha256":os.environ["FRA_SOURCE_SHA256"],
 "reviewed_at_utc":"2026-11-22T00:00:00+00:00",
 "checks":{k:True for k in json.loads(os.environ["FRA_REQUIRED_CHECKS"])},
 "artifacts":artifacts,"limitations":["Synthetic data, not semantic film verification"]}
(out/"evidence.json").write_text(json.dumps(doc))
'''

def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)

def call(*argv: str, success: bool, label: str, records: list[dict]) -> dict:
    command=[sys.executable,"-B","-m","engine21",*map(str,argv)]
    p=subprocess.run(command,cwd=REPO,capture_output=True,text=True,
                     encoding="utf8",timeout=150,check=False)
    good=p.returncode==0 if success else p.returncode!=0
    records.append({"step":label,"passed":good,"exit_code":p.returncode,
                    "stdout":p.stdout[-1200:],"stderr":p.stderr[-1000:]})
    check(good,label+" unexpected exit "+str(p.returncode)+" "+p.stderr[-300:])
    return json.loads(p.stdout) if success and p.stdout.strip() else {}

def sign(job_id:str, gate:str, digest:str, key:bytes) -> dict:
    now=datetime.now(timezone.utc)
    payload={"job_id":job_id,"gate":gate,"subject_sha256":digest,
             "issued_at_utc":now.isoformat(),
             "expires_at_utc":(now+timedelta(minutes=3)).isoformat()}
    signature=hmac.new(key,json.dumps(payload,sort_keys=True,ensure_ascii=False,
                 separators=(",",":")).encode(),hashlib.sha256).hexdigest()
    return {**payload,"signature":signature}

def adapter_config(path:Path, script:Path, stages:list[str],
                   *,timeout:float=20,max_attempts:int=2)->None:
    data={"schema_version":"2.1.0","stages":{
      stage:{"executable":sys.executable,"argv":[str(script)],
             "timeout_seconds":timeout,"max_attempts":max_attempts,
             "retry_safe":True} for stage in stages}}
    path.write_text(json.dumps(data,indent=2),encoding="utf8")

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--qa-root",type=Path,required=True)
    args=parser.parse_args()
    qa_root=args.qa_root.resolve(strict=True)
    check(qa_root.name.startswith("__ENGINE21_QA_"),
          "Refuse to run outside explicitly isolated QA root")
    run=qa_root/"runs"/("qa-"+uuid.uuid4().hex[:12])
    run.mkdir(parents=True)
    trusted=run/"trusted";trusted.mkdir()
    records=[]
    summary={"schema_version":1,"machine":os.environ.get("COMPUTERNAME","unknown"),
             "started_at_utc":datetime.now(timezone.utc).isoformat(),
             "run_root":str(run),"mode":"synthetic; real Windows CLI + FFmpeg",
             "checks":records,"source_sha256":None}
    try:
        movie=run/"synthetic_source.mp4"
        p=subprocess.run(["ffmpeg","-nostdin","-v","error",
           "-f","lavfi","-i","color=c=black:s=160x90:r=12:d=1.2",
           "-f","lavfi","-i","sine=frequency=500:sample_rate=16000:duration=1.2",
           "-shortest","-c:v","mpeg4","-c:a","aac","-y",str(movie)],
           capture_output=True,text=True,timeout=30,check=False)
        check(p.returncode==0,"Cannot create synthetic movie: "+p.stderr[-250:])
        summary["source_sha256"]=state.sha256(movie)
        code=trusted/"fixture_adapter.py";code.write_text(ADAPTER,encoding="utf8")
        config=trusted/"adapters.json"
        adapter_config(config,code,list(state.STAGES))
        job=jobctl.create_job(movie,run/"jobs","Synthetic Windows QA",probe=False)
        call("init","--job",str(job),"--config",str(config),
             success=True,label="init and pin config",records=records)
        call("run","--job",str(job),"--config",str(config),"--stage","N01",
             success=False,label="dependency N01 blocks before N00",records=records)
        for stage in ("N00","N01","N02","N03","N04","N05"):
            result=call("run","--job",str(job),"--config",str(config),"--stage",stage,
                        success=True,label="real CLI "+stage,records=records)
            check(result["status"]=="DONE",stage+" not DONE")
        sample=job/"voice"/"approved_sample.wav"
        sample.parent.mkdir(exist_ok=True)
        create=subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
             "-i","sine=frequency=520:duration=0.5","-y",str(sample)],
             capture_output=True,text=True,timeout=30)
        check(create.returncode==0,"Could not generate synthetic voice WAV")
        call("run","--job",str(job),"--config",str(config),"--stage","N06",
             success=False,label="N06 denies no approval",records=records)
        s=state.reconcile(job)
        key=b"TEST_ONLY_not_human_approval_key_2026"
        keyfile=trusted/"test-only-key";keyfile.write_bytes(key)
        approvals=trusted/"receipts";approvals.mkdir()
        job_id=jobctl.read_job(job)["job_id"]
        digest=s["stages"]["N05"]["evidence_sha256"]
        forged=sign(job_id,"script",digest,b"wrong-test-only-key_123456")
        (approvals/"script.json").write_text(json.dumps(forged),encoding="utf8")
        (approvals/"voice.json").write_text(json.dumps(
             sign(job_id,"voice",state.sha256(sample),key)),encoding="utf8")
        args_auth=("run","--job",str(job),"--config",str(config),
                   "--receipts-dir",str(approvals),"--host-key-file",str(keyfile))
        call(*args_auth,"--stage","N06",success=False,
             label="forged HMAC denies N06",records=records)
        (approvals/"script.json").write_text(json.dumps(
             sign(job_id,"script",digest,key)),encoding="utf8")
        result=call(*args_auth,"--stage","N06",success=True,
                    label="test-only signed N06 plus true WAV decode",records=records)
        check(result["status"]=="DONE","N06 not DONE")
        result=call("run","--job",str(job),"--config",str(config),"--stage","N07",
                    success=True,label="N07 synthetic semantic map gate",records=records)
        check(result["status"]=="DONE","N07 not DONE")
        call(*args_auth,"--stage","N08",success=False,
             label="N08 blocks without pilot approval",records=records)
        pilot=job/"edit"/"pilot.mp4";pilot.parent.mkdir(exist_ok=True)
        shutil.copy2(movie,pilot)
        (approvals/"pilot.json").write_text(json.dumps(
             sign(job_id,"pilot",state.sha256(pilot),key)),encoding="utf8")
        for stage in ("N08","N09"):
            result=call(*args_auth,"--stage",stage,success=True,
                        label=stage+" actual H264-or-MPEG4 MP4/AAC decode",records=records)
            check(result["status"]=="DONE",stage+" not DONE")
        s=call("inspect","--job",str(job),success=True,
               label="all completed and valid",records=records)
        check(all(s["stages"][x]["status"]=="DONE" for x in state.STAGES),
              "Not all ten stages DONE")
        # Corrupt a completed intermediate output and verify every dependent stage becomes stale.
        artifact=job/s["stages"]["N01"]["artifacts"][0]["path"]
        artifact.write_text('{"tampered":true}\n',encoding="utf8")
        s=call("inspect","--job",str(job),success=True,
               label="artifact tamper invalidates descendants",records=records)
        check(s["stages"]["N01"]["status"]=="STALE","N01 not stale")
        check(s["stages"]["N09"]["status"]=="STALE","downstream N09 not stale")
        check(s["stages"]["N02"]["status"]=="DONE","independent N02 wrongly stale")
        movie.write_bytes(b"tampered synthetic source only")
        s=call("inspect","--job",str(job),success=True,
               label="source hash tamper denies all completed",records=records)
        check(s["source_intact"] is False,"source tamper not detected")
        check(s["stages"]["N02"]["status"]=="STALE","source tamper did not stale N02")
        # Separate job: simulate a crash with N01 RUNNING, then recover to attempt #2.
        clean=run/"recovery_source.mp4"
        shutil.copy2(job/"edit"/"pilot.mp4",clean)
        recover_job=jobctl.create_job(clean,run/"recover_jobs","Crash recovery",probe=False)
        call("init","--job",str(recover_job),"--config",str(config),
             success=True,label="recovery job init",records=records)
        call("run","--job",str(recover_job),"--config",str(config),"--stage","N00",
             success=True,label="recovery job N00",records=records)
        rec=state.read_state(recover_job)
        rec["stages"]["N01"].update(status="RUNNING",attempts=1)
        state.atomic_state(recover_job,rec)
        rec=call("inspect","--job",str(recover_job),success=True,
                 label="interrupted RUNNING becomes INTERRUPTED",records=records)
        check(rec["stages"]["N01"]["status"]=="INTERRUPTED","crash not recovered")
        rec=call("run","--job",str(recover_job),"--config",str(config),"--stage","N01",
                 success=True,label="safe retry succeeds attempt 2",records=records)
        check(rec["attempts"]==2 and rec["status"]=="DONE","safe retry wrong count")
        # Distinct job and trusted config: kill overlong Python task.
        sleeper=trusted/"sleep_adapter.py";sleeper.write_text("import time\ntime.sleep(4)\n")
        slowconf=trusted/"slow-adapters.json"
        adapter_config(slowconf,sleeper,["N00"],timeout=1,max_attempts=1)
        timeout_job=jobctl.create_job(clean,run/"timeout_jobs","Timeout scenario",probe=False)
        call("run","--job",str(timeout_job),"--config",str(slowconf),"--stage","N00",
             success=False,label="actual subprocess timeout fails closed",records=records)
        rec=call("inspect","--job",str(timeout_job),success=True,
                 label="timeout remains FAILED",records=records)
        check(rec["stages"]["N00"]["status"]=="FAILED","timeout not FAILED")
        if os.name=="nt":
            # Junctions are normally creatable without Developer Mode / symlink privilege.
            outside=run/"junction_target";outside.mkdir()
            junction_job=jobctl.create_job(clean,run/"junction_jobs","Junction escape",probe=False)
            junction=junction_job/".engine21"
            link=subprocess.run(["cmd.exe","/c","mklink","/J",str(junction),str(outside)],
                capture_output=True,text=True,timeout=15)
            if link.returncode==0:
                call("init","--job",str(junction_job),"--config",str(config),
                    success=False,label="Windows junction path escape blocked",records=records)
                check(not (outside/"engine.lock").exists(),
                      "Engine lock unexpectedly written through junction")
            else:
                records.append({"step":"Windows junction creation unavailable",
                   "passed":True,"skipped":True,"exit_code":link.returncode,
                   "stderr":link.stderr[-250:]})
        summary["status"]="PASS"
        summary["passed_cases"]=len(records)
        summary["test_only_approval"]=True
        print("WINDOWS_ENGINE21_ACCEPTANCE_PASS checks="+str(len(records)))
        return 0
    except BaseException as exc:
        summary["status"]="FAIL"
        summary["error"]=type(exc).__name__+": "+str(exc)
        print("WINDOWS_ENGINE21_ACCEPTANCE_FAIL",summary["error"],file=sys.stderr)
        return 1
    finally:
        summary["finished_at_utc"]=datetime.now(timezone.utc).isoformat()
        report=run/"qa_result.json"
        report.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
        print("QA_REPORT="+str(report))

if __name__=="__main__":
    raise SystemExit(main())