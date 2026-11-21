"""Real local model workers through Engine21; synthetic source, test approvals ONLY.

No packages, model weights or film data installed/downloaded/copied.
The test-only HMAC signer here MUST NEVER be used for real user approval.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timedelta,timezone
import hashlib,hmac,json,os
from pathlib import Path
import shutil,subprocess,sys,time,uuid

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))
sys.path.insert(0,str(REPO/"skills"/"film-review-orchestrator"/"scripts"))
import jobctl
from engine21 import state
from stage3.framework import sha256,runtime_digest
from stage3.media import decode,probe
from stage4.media import loop_source_with_voice
from stage4.approval_requests import make_request,save_request

MODELS={
 "N02":("asr","asr/faster-whisper-large-v3-turbo/model.bin"),
 "N03":("vision","vision/qwen3-vl-2b-instruct/model.safetensors"),
 "N04":("system",None),
 "N05":("system",None),
 "N06":("tts","tts/vieneu-v3-turbo/update/model.safetensors"),
 "N07":("vision","embeddings/clip-vit-base-patch32/pytorch_model.bin"),
 "N08":("system",None),
 "N09":("system",None),
}

def pinned_code_inputs(repo_root:Path,worker:Path)->dict[str,str]:
    """Pin worker and ALL directly imported Stage4/semantic QC code by SHA."""
    base=Path(repo_root).resolve(strict=True)
    deps=[Path(worker),*sorted((base/"stage4").glob("*.py")),
          base/"skills"/"film-review-orchestrator"/"scripts"/"evidence_qc.py"]
    if len(deps)<4:
        raise ValueError("Stage4 worker dependencies missing; refuse unpinned worker")
    return {str(p.resolve(strict=True)):sha256(p.resolve(strict=True)) for p in deps}

def check(test,reason):
    if not test:raise AssertionError(reason)

def sign(job,gate,subject,key):
    now=datetime.now(timezone.utc)
    data={"job_id":job,"gate":gate,"subject_sha256":subject,
      "issued_at_utc":now.isoformat(),
      "expires_at_utc":(now+timedelta(minutes=5)).isoformat()}
    sig=hmac.new(key,json.dumps(data,ensure_ascii=False,sort_keys=True,
             separators=(",",":")).encode("utf8"),hashlib.sha256).hexdigest()
    return {**data,"signature":sig}

def call(stage,argv,log:list,expect_success=True):
    start=time.monotonic()
    cmd=[sys.executable,"-B","-m","engine21",*map(str,argv)]
    cp=subprocess.run(cmd,cwd=REPO,stdin=subprocess.DEVNULL,
       stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf8",timeout=900)
    succeeded=cp.returncode==0
    item={"stage":stage,"exit":cp.returncode,
        "runtime_seconds":round(time.monotonic()-start,2),
        "stdout_tail":cp.stdout[-1800:],"stderr_tail":cp.stderr[-1800:],
        "expected_success":expect_success}
    log.append(item)
    if succeeded!=expect_success:
        raise RuntimeError("Engine command unexpected outcome "+stage+
          " exit="+str(cp.returncode)+" "+cp.stderr[-1000:]+cp.stdout[-600:])
    return json.loads(cp.stdout) if succeeded and cp.stdout.strip() else {}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--qa-root",type=Path,required=True)
    parser.add_argument("--legacy-root",type=Path,required=True)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--voice-sample",type=Path,required=True)
    args=parser.parse_args()
    root=args.qa_root.resolve(strict=True)
    check(root.name=="__FRA_PHASE4_NARRATIVE_20261122","QA root must be the preauthorized isolated Phase4 workspace")
    legacy=args.legacy_root.resolve(strict=True)
    models=legacy/"models"
    source=args.source.resolve(strict=True)
    sample=args.voice_sample.resolve(strict=True)
    check(models.is_dir() and source.is_file() and sample.is_file(),"Required local model/source/voice unavailable")
    if source.is_relative_to(legacy):
        raise PermissionError("QA input source must be synthetic and OUTSIDE legacy folder")
    run=root/"runs"/("real-engine-"+uuid.uuid4().hex[:10])
    run.mkdir(parents=True,exist_ok=False)
    trust=run/"trusted";trust.mkdir()
    records=[]
    summary={"qa_mode":"REAL_LOCAL_INFERENCE_ON_SYNTHETIC_MEDIA",
      "human_approval":"TEST-ONLY_FAKE_SIGNER",
      "status":"RUNNING","stages":[],"started_at_utc":datetime.now(timezone.utc).isoformat(),
      "machine":os.environ.get("COMPUTERNAME"),"run_root":str(run)}
    try:
        installed={
          "system":sys.executable,
          "asr":str(legacy/".venv"/"Scripts"/"python.exe"),
          "vision":str(legacy/"tools"/"vision"/".venv"/"Scripts"/"python.exe"),
          "tts":str(legacy/"tools"/"vieneu"/".venv"/"Scripts"/"python.exe"),
        }
        worker=REPO/"qa"/"legacy_offline_worker.py"
        check(worker.is_file(),"QA worker not found")
        pinned_inputs=pinned_code_inputs(REPO,worker)
        configs={}
        for stage,(venv,weightrel) in MODELS.items():
            exe=Path(installed[venv]).resolve(strict=True)
            files=dict(pinned_inputs)
            if weightrel:
                weight=models/weightrel
                if not weight.is_file():raise FileNotFoundError("Model weight absent "+weightrel)
                files[str(weight)]=sha256(weight)
            conf={"schema_version":"3.0","stages":{
              stage:{"executable":str(exe),"argv":["-B",str(worker),
                       "--stage",stage,"--models-root",str(models)],
                     "executable_sha256":sha256(exe),
                     "timeout_seconds":480,"input_files":files}}}
            path=trust/(stage+"-provider.json")
            path.write_text(json.dumps(conf,indent=2),encoding="utf8")
            configs[stage]=path
        engine_config={"schema_version":"2.1.0","stages":{}}
        for st in state.STAGES:
            argv=["-B",str(REPO/"stage3_adapter.py"),
                   "--mode","production","--runtime-sha256",runtime_digest()]
            if st in configs:argv+=["--provider-config",str(configs[st])]
            engine_config["stages"][st]={
                "executable":sys.executable,"argv":argv,
                "timeout_seconds":600,"max_attempts":1,"retry_safe":True}
        config_path=trust/"engine-adapters.json"
        config_path.write_text(json.dumps(engine_config,indent=2),encoding="utf8")
        job=jobctl.create_job(source,run/"jobs","Real Local Models Synthetic QA",probe=False)
        summary["job_path"]=str(job)
        prefix=("run","--job",str(job),"--config",str(config_path))
        call("init",("init","--job",str(job),"--config",str(config_path)),records)
        # N00/N01 run real FFmpeg, and N02/N03 run real local AI.
        for st in ("N00","N01","N02","N03","N04","N05"):
            out=call(st,(*prefix,"--stage",st),records)
            check(out.get("status")=="DONE",st+" not DONE")
        script_evidence=state.reconcile(job)["stages"]["N05"]["evidence_sha256"]
        key=b"TEST_ONLY_HMAC_NOT_HUMAN_APPROVAL_FOR_LOCAL_MODEL_QA"
        hostkey=trust/"qa-only-signing-key";hostkey.write_bytes(key)
        receipts=trust/"receipts";receipts.mkdir()
        sample_dest=job/"voice"/"approved_sample.wav"
        sample_dest.parent.mkdir(exist_ok=True)
        shutil.copy2(sample,sample_dest)
        job_id=jobctl.read_job(job)["job_id"]
        (receipts/"script.json").write_text(json.dumps(sign(job_id,"script",script_evidence,key)),encoding="utf8")
        (receipts/"voice.json").write_text(json.dumps(sign(job_id,"voice",sha256(sample_dest),key)),encoding="utf8")
        approved=(*prefix,"--receipts-dir",str(receipts),"--host-key-file",str(hostkey))
        # Missing approvals fail closed, even with installed real TTS.
        missing=call("N06_expected_block",(*prefix,"--stage","N06"),records,expect_success=False)
        for st in ("N06","N07"):
            out=call(st,(*approved,"--stage",st),records)
            check(out.get("status")=="DONE",st+" not DONE")
        voice_art=next(x for x in state.read_state(job)["stages"]["N06"]["artifacts"]
                       if Path(x["path"]).name=="narration.wav")
        voice_path=job/voice_art["path"]
        voice_props=decode(voice_path,need_audio=True)
        approved_pilot=job/"edit"/"pilot.mp4"
        approved_pilot.parent.mkdir(exist_ok=True)
        loop_source_with_voice(source,voice_path,approved_pilot)
        (receipts/"pilot.json").write_text(json.dumps(
             sign(job_id,"pilot",sha256(approved_pilot),key)),encoding="utf8")
        call("N08_expected_block",(*prefix,"--stage","N08"),records,expect_success=False)
        for st in ("N08","N09"):
            out=call(st,(*approved,"--stage",st),records)
            check(out.get("status")=="DONE",st+" not DONE")
        st=state.reconcile(job)
        check(all(st["stages"][s]["status"]=="DONE" for s in state.STAGES),
              "Not all 10 stages verified DONE")
        providers={}
        for stg in MODELS:
            evidence=st["stages"][stg]["evidence_path"]
            attempt=(job/evidence).parent
            doc=json.loads((attempt/"provider_verification.json").read_text(encoding="utf8"))
            providers[stg]=doc["model_id"]
            check(doc.get("input_media_synthetic") and doc.get("qa_only"),
                 "Worker falsely claims real-film production provenance")
        for stg in ("N02","N03","N06","N07"):
            check("local-" in providers[stg],"Real AI provider not reported for "+stg)
        final=next(job/x["path"] for x in st["stages"]["N09"]["artifacts"]
                   if Path(x["path"]).name=="final_review.mp4")
        final_props=decode(final,need_audio=True,need_video=True)
        if abs(final_props["duration_s"]-voice_props["duration_s"])>0.11:
            raise AssertionError("QA pilot truncated TTS narration")
        n05=next(job/x["path"] for x in st["stages"]["N05"]["artifacts"]
                 if Path(x["path"]).name=="sentence_claims.jsonl")
        n07=next(job/x["path"] for x in st["stages"]["N07"]["artifacts"]
                 if Path(x["path"]).name=="sentence_shot_map.json")
        claim=json.loads(n05.read_text(encoding="utf8").splitlines()[0])
        mapping=json.loads(n07.read_text(encoding="utf8"))
        mapped=mapping["sentences"][0]
        if (mapped["atomic_claims"]!=claim["atomic_claims"]
            or mapped["review_text"]!=claim["review_text"]
            or mapped["sentence_id"]!=claim["sentence_id"]):
            raise AssertionError("N07 substituted evidence or review from N05")
        requests={}
        for gate in ("script","voice","pilot"):
            unsigned=make_request(job,gate)
            if "signature" in unsigned or unsigned["human_approved"] is not False:
                raise AssertionError("Agent created false human approval")
            requests[gate]=save_request(job,unsigned).name
        summary.update({"status":"PASS","cases":len(records),"model_providers":providers,
            "unsigned_approval_requests":requests,
            "n05_n07_claim_ids_match":True,
            "voice_preserved_full_duration":True,
            "voice_duration_s":voice_props["duration_s"],
            "final_mp4_sha256":sha256(final),
            "final_mp4_duration_s":final_props["duration_s"],
            "final_mp4_bytes":final.stat().st_size,
            "final_mp4_streams":final_props["stream_types"],
            "qa_synthetic_source_sha256":sha256(source),
            "all_10_engine_stages_DONE":True,
            "real_story_creative_model":False,
            "genuine_human_approval":False})
        print("ENGINE21_REAL_LOCAL_MODELS_SYNTHETIC_PASS",len(records),flush=True)
        return 0
    except BaseException as exc:
        summary.update({"status":"FAIL","reason":type(exc).__name__+": "+str(exc),
                        "cases":len(records)})
        print("ENGINE21_REAL_LOCAL_MODELS_SYNTHETIC_FAIL",
              summary["reason"],file=sys.stderr,flush=True)
        return 1
    finally:
        summary["ended_at_utc"]=datetime.now(timezone.utc).isoformat()
        summary["stages"]=records
        (run/"report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
        print("RUN_REPORT="+str(run/"report.json"),flush=True)

if __name__=="__main__":
    raise SystemExit(main())
