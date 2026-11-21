#!/usr/bin/env python3
"""Phase3: real Engine 2.1 N00-N09, synthetic data and test-only approvals."""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import hashlib,hmac,json,os
from pathlib import Path
import shutil,subprocess,sys,uuid

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))
sys.path.insert(0,str(REPO/"skills"/"film-review-orchestrator"/"scripts"))
import jobctl
from engine21 import state
from stage3.framework import sha256,runtime_digest
from stage3.media import decode

def assert_true(ok, detail):
    if not ok:raise AssertionError(detail)

def run_cli(args, *,expect=0,records=None):
    cmd=[sys.executable,"-B","-m","engine21",*map(str,args)]
    r=subprocess.run(cmd,cwd=REPO,stdin=subprocess.DEVNULL,
                     capture_output=True,text=True,encoding="utf8",timeout=120)
    good=r.returncode==expect
    if records is not None:
        records.append({"command":" ".join(str(x) for x in args[:2]),
                        "stage":next((args[i+1] for i,x in enumerate(args[:-1])
                                      if x=="--stage"),None),
                        "status":"PASS" if good else "FAIL",
                        "exit_code":r.returncode,"expected_exit_code":expect,
                        "stderr_last":r.stderr[-250:]})
    if not good:
        raise AssertionError("CLI return "+str(r.returncode)+" expected "+str(expect)+" "+r.stderr[-500:])
    return json.loads(r.stdout) if r.stdout.strip() else {}

def approval(job_id,gate,digest,key):
    now=datetime.now(timezone.utc)
    fields={"job_id":job_id,"gate":gate,"subject_sha256":digest,
      "issued_at_utc":now.isoformat(),
      "expires_at_utc":(now+timedelta(minutes=3)).isoformat()}
    sig=hmac.new(key,json.dumps(fields,ensure_ascii=False,sort_keys=True,
                 separators=(",",":")).encode(),hashlib.sha256).hexdigest()
    return {**fields,"signature":sig}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--qa-root",type=Path,required=True)
    args=p.parse_args(argv)
    root=args.qa_root.resolve(strict=True)
    assert_true(root.name=="__FRA_PHASE3_20261122","Not an explicitly authorized isolated QA root")
    scratch=root/"runs"/("stage3-"+uuid.uuid4().hex[:9])
    scratch.mkdir(parents=True,exist_ok=False)
    records=[]
    summary={"schema_version":1,"mode":"SYNTHETIC_NO_AI_INFERENCE",
       "machine":os.environ.get("COMPUTERNAME","unknown"),
       "started_at_utc":datetime.now(timezone.utc).isoformat(),
       "report_location":str(scratch/"acceptance.json"),
       "records":records}
    try:
        source=scratch/"synthetic_source.mp4"
        gen=subprocess.run(["ffmpeg","-nostdin","-v","error",
            "-f","lavfi","-i","color=c=blue:s=320x180:r=12:d=1.4",
            "-f","lavfi","-i","sine=frequency=530:duration=1.4",
            "-shortest","-c:v","mpeg4","-c:a","aac","-y",str(source)],
            capture_output=True,timeout=45)
        assert_true(gen.returncode==0,"cannot generate synthetic media")
        summary["source_sha256"]=sha256(source)
        trusted=scratch/"trusted";trusted.mkdir()
        adapter=REPO/"stage3_adapter.py"
        config=trusted/"engine-adapters.json"
        config.write_text(json.dumps({"schema_version":"2.1.0",
          "stages":{stage:{"executable":sys.executable,
            "argv":["-B",str(adapter),"--mode","synthetic",
                    "--runtime-sha256",runtime_digest()],
            "timeout_seconds":120,"max_attempts":2,"retry_safe":True}
            for stage in state.STAGES}},indent=2),encoding="utf8")
        job=jobctl.create_job(source,scratch/"jobs","Phase3 Synthetic",probe=False)
        summary["job"]=str(job)
        generic=("run","--job",str(job),"--config",str(config))
        run_cli(("init","--job",str(job),"--config",str(config)),records=records)
        run_cli((*generic,"--stage","N01"),expect=2,records=records)
        for stage in state.STAGES[:6]:
            result=run_cli((*generic,"--stage",stage),records=records)
            assert_true(result["status"]=="DONE",stage+" not DONE")
        sample=job/"voice"/"approved_sample.wav"
        sample.parent.mkdir(exist_ok=True)
        create=subprocess.run(["ffmpeg","-nostdin","-v","error","-f","lavfi",
          "-i","sine=frequency=480:duration=0.5","-y",str(sample)],capture_output=True,timeout=30)
        assert_true(create.returncode==0,"cannot create voice approval sample")
        decode(sample,need_audio=True)
        receipts=trusted/"receipts";receipts.mkdir()
        key=b"TEST_ONLY_not_actual_human_approval_secret_v3"
        keyfile=trusted/"test-signing-key";keyfile.write_bytes(key)
        safe=("run","--job",str(job),"--config",str(config),
              "--receipts-dir",str(receipts),"--host-key-file",str(keyfile))
        run_cli((*generic,"--stage","N06"),expect=2,records=records)
        current=state.reconcile(job)
        job_id=jobctl.read_job(job)["job_id"]
        script_hash=current["stages"]["N05"]["evidence_sha256"]
        (receipts/"script.json").write_text(json.dumps(
            approval(job_id,"script",script_hash,b"wrong-test-key-123456789")))
        (receipts/"voice.json").write_text(json.dumps(
            approval(job_id,"voice",sha256(sample),key)))
        run_cli((*safe,"--stage","N06"),expect=2,records=records)
        (receipts/"script.json").write_text(json.dumps(approval(job_id,"script",script_hash,key)))
        done=run_cli((*safe,"--stage","N06"),records=records)
        assert_true(done["status"]=="DONE","N06")
        done=run_cli((*generic,"--stage","N07"),records=records)
        assert_true(done["status"]=="DONE","N07")
        run_cli((*generic,"--stage","N08"),expect=2,records=records)
        pilot_preview=job/"edit"/"pilot.mp4";pilot_preview.parent.mkdir(exist_ok=True)
        shutil.copy2(source,pilot_preview)
        (receipts/"pilot.json").write_text(json.dumps(
            approval(job_id,"pilot",sha256(pilot_preview),key)))
        for stage in ("N08","N09"):
            done=run_cli((*safe,"--stage",stage),records=records)
            assert_true(done["status"]=="DONE",stage)
        current=run_cli(("inspect","--job",str(job)),records=records)
        assert_true(all(current["stages"][stage]["status"]=="DONE" for stage in state.STAGES),
                    "not all 10 stages done")
        final=job/current["stages"]["N09"]["artifacts"][0]["path"]
        props=decode(final,need_video=True,need_audio=True)
        assert_true(props["duration_s"]>0.2,"final duration invalid")
        semantic=job/current["stages"]["N09"]["artifacts"][2]["path"]
        assert_true(json.loads(semantic.read_text())["semantic_verified"] is False,
            "Fixture output must NEVER claim semantic verification")
        summary["final_media"]={"sha256":sha256(final),"duration_s":props["duration_s"],
                                 "bytes":final.stat().st_size,"stream_types":props["stream_types"]}
        n01=job/current["stages"]["N01"]["artifacts"][0]["path"]
        n01.write_text('{"tampered":true}\n')
        check=run_cli(("inspect","--job",str(job)),records=records)
        assert_true(check["stages"]["N01"]["status"]=="STALE",
                    "N01 corrupted source did not invalidate stage")
        assert_true(check["stages"]["N09"]["status"]=="STALE",
                    "N09 dependent did not invalidate")
        assert_true(check["stages"]["N02"]["status"]=="DONE",
                    "Independent stage incorrectly invalidated")
        source.write_bytes(b"synthetic source tampered")
        check=run_cli(("inspect","--job",str(job)),records=records)
        assert_true(check["source_intact"] is False,"changed synthetic original source accepted")
        summary.update(status="PASS",cases=len(records))
        print("PHASE3_SYNTHETIC_ACCEPTANCE_PASS",len(records))
        return 0
    except BaseException as exc:
        summary.update(status="FAIL",reason=type(exc).__name__+": "+str(exc),
                       cases=len(records))
        print("PHASE3_SYNTHETIC_ACCEPTANCE_FAIL",summary["reason"],file=sys.stderr)
        return 1
    finally:
        summary["finished_at_utc"]=datetime.now(timezone.utc).isoformat()
        (scratch/"acceptance.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False))
        print("ACCEPTANCE_REPORT="+str(scratch/"acceptance.json"))

if __name__=="__main__":
    raise SystemExit(main())
