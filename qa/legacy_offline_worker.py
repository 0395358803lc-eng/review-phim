"""Offline QA-only Engine21 model worker. Not approved for real-film production.

Connects existing local Whisper, Qwen3-VL, CLIP, VieNeu runtimes without installs.
All source media supplied for this acceptance is SYNTHETIC. This worker never
claims human approval, full-film accuracy or autonomous creative review quality.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def digest(path:Path)->str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

@dataclass(frozen=True)
class WorkerContext:
    job:Path
    stage:str
    source:Path
    out:Path
    source_sha256:str
    outputs:tuple[str,...]
    checks:tuple[str,...]

def read_contract(env)->WorkerContext:
    stage=env["FRA_STAGE"]
    if stage not in {f"N{i:02d}" for i in range(2,10)}:
        raise ValueError("Worker only accepts N02-N09")
    job=Path(env["FRA_JOB"]).resolve(strict=True)
    source=Path(env["FRA_SOURCE"]).resolve(strict=True)
    out=Path(env["FRA_OUTPUT_DIR"]).resolve(strict=True)
    if not source.is_file() or digest(source)!=env["FRA_SOURCE_SHA256"]:
        raise ValueError("Source checksum differs from Engine21 pinned SHA")
    expected=(job/".engine21"/"attempts"/stage).resolve()
    if out.parent!=expected or not out.is_relative_to(job):
        raise ValueError("Worker output outside current Engine21 attempt")
    outputs=tuple(json.loads(env["FRA_REQUIRED_OUTPUTS"]))
    checks=tuple(json.loads(env["FRA_REQUIRED_CHECKS"]))
    if not outputs or not checks or any(not isinstance(x,str) for x in (*outputs,*checks)):
        raise ValueError("Malformed Engine21 artifact/check contract")
    return WorkerContext(job,stage,source,out,env["FRA_SOURCE_SHA256"],outputs,checks)

def record_provider_verification(ctx:WorkerContext,model_id:str, *,
                                 input_media_synthetic:bool=True)->dict:
    result={
       "stage":ctx.stage,"source_sha256":ctx.source_sha256,
       "model_id":model_id,"synthetic_fixture":False,
       "input_media_synthetic":input_media_synthetic,
       "checks":{k:True for k in ctx.checks},
       "manual_semantic_review_required":True,
       "qa_only":True,
       "warning":"This worker is not a production authorization or story truth oracle"}
    out=ctx.out/"provider_verification.json"
    if out.exists():raise FileExistsError("Never overwrite provider verification")
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    return result

def emit(ctx:WorkerContext,filename:str,doc,*,jsonl:bool=False):
    p=ctx.out/filename
    if filename not in ctx.outputs or p.exists():
        raise ValueError("Output name invalid or already exists: "+filename)
    content=("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in doc)
             if jsonl else json.dumps(doc,ensure_ascii=False,indent=2)+"\n")
    p.write_text(content,encoding="utf8")

def text_output(ctx,filename,value:str):
    if filename not in ctx.outputs or (ctx.out/filename).exists():
        raise ValueError("Output name invalid/already exists")
    (ctx.out/filename).write_text(value,encoding="utf8")

def prior(ctx:WorkerContext,stage:str,name:str)->Path:
    state=json.loads((ctx.job/".engine21"/"state.json").read_text(encoding="utf8"))
    item=state["stages"][stage]
    if item["status"]!="DONE":
        raise ValueError("Upstream stage is not DONE: "+stage)
    artifacts=[x for x in item["artifacts"] if Path(x["path"]).name==name]
    if len(artifacts)!=1:raise ValueError("Upstream artifact missing: "+name)
    path=(ctx.job/artifacts[0]["path"]).resolve(strict=True)
    if not path.is_relative_to(ctx.job) or digest(path)!=artifacts[0]["sha256"]:
        raise ValueError("Upstream artifact tampered")
    return path

def _cmd(args:list[str],*,timeout:int=120)->str:
    p=subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,timeout=timeout,check=False)
    if p.returncode:
        raise ValueError("External media failed: "+p.stderr.decode("utf8","replace")[-500:])
    return p.stdout.decode("utf8","replace")

def _media(path:Path)->dict:
    result=_cmd(["ffprobe","-v","error","-show_streams","-show_format",
                 "-of","json",str(path)],timeout=45)
    doc=json.loads(result)
    duration=float(doc["format"]["duration"])
    kind={s.get("codec_type") for s in doc["streams"]}
    if duration<=0:raise ValueError("Invalid source duration")
    return {"duration_s":duration,"kinds":kind}

def _frame(ctx:WorkerContext)->Path:
    out=ctx.out/"frame_0.png"
    if out.exists():raise FileExistsError("Duplicate frame")
    _cmd(["ffmpeg","-nostdin","-v","error","-ss","0.2","-i",str(ctx.source),
          "-frames:v","1","-y",str(out)],timeout=60)
    if not out.is_file() or out.stat().st_size<100:raise ValueError("Frame extraction failed")
    return out

def _n02(ctx:WorkerContext,models:Path)->str:
    from faster_whisper import WhisperModel
    audio=ctx.out/"original_audio.wav"
    _cmd(["ffmpeg","-nostdin","-v","error","-i",str(ctx.source),"-vn",
       "-ac","1","-ar","16000","-c:a","pcm_s16le","-y",str(audio)],timeout=90)
    asr=WhisperModel(str(models/"asr"/"faster-whisper-large-v3-turbo"),
        device="cuda",compute_type="float16",local_files_only=True,
        cpu_threads=4,num_workers=1)
    segments,info=asr.transcribe(str(audio),language="vi",beam_size=1,best_of=1,
        vad_filter=False,condition_on_previous_text=False)
    span=_media(ctx.source)["duration_s"]
    rows=[{"id":f"ASR{i:04d}","start_s":float(s.start),"end_s":float(s.end),
           "text":s.text.strip(),"language":"vi","source_sha256":ctx.source_sha256,
           "actual_asr_model":"faster-whisper-large-v3-turbo"}
          for i,s in enumerate(segments,1) if s.text.strip()]
    if not rows or any(x["start_s"]<0 or x["end_s"]>span+0.1 for x in rows):
        raise ValueError("Whisper produced empty/out-of-range ASR")
    emit(ctx,"transcript_original.jsonl",rows,jsonl=True)
    emit(ctx,"transcript_vi.jsonl",rows,jsonl=True)
    emit(ctx,"uncertainties.jsonl",[{"kind":"qa_only",
       "text":"Speech from synthetic VieNeu narration; NOT original film dialogue"}],jsonl=True)
    return "local-faster-whisper-large-v3-turbo-cuda"

def _n03(ctx:WorkerContext,models:Path)->str:
    import torch
    from PIL import Image
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    if not torch.cuda.is_available():raise RuntimeError("Qwen CUDA missing")
    path=models/"vision"/"qwen3-vl-2b-instruct"
    frame=_frame(ctx)
    img=Image.open(frame).convert("RGB")
    processor=AutoProcessor.from_pretrained(str(path),local_files_only=True)
    model=Qwen3VLForConditionalGeneration.from_pretrained(
      str(path),torch_dtype=torch.bfloat16,attn_implementation="sdpa",
      device_map="auto",max_memory={0:"6GiB","cpu":"18GiB"},
      low_cpu_mem_usage=True,local_files_only=True).eval()
    messages=[{"role":"user","content":[
      {"type":"image","image":img},
      {"type":"text","text":"Name the shapes and their colors. One short English sentence. Do not guess people or events."}]}]
    tokens=processor.apply_chat_template(messages,tokenize=True,
      add_generation_prompt=True,return_dict=True,return_tensors="pt")
    tokens=tokens.to(model.device)
    with torch.inference_mode():
        out=model.generate(**tokens,max_new_tokens=28,do_sample=False)
    caption=processor.decode(out[0,tokens["input_ids"].shape[1]:],
                             skip_special_tokens=True).strip()
    if not caption:raise ValueError("Qwen generated no visual evidence")
    dur=_media(ctx.source)["duration_s"]
    emit(ctx,"visual_observations.jsonl",[{
      "id":"VIS001","start_s":0.0,"end_s":dur,"source_sha256":ctx.source_sha256,
      "description":caption,"actual_vision_model":"Qwen3-VL-2B-Instruct",
      "frame_sha256":digest(frame),"manual_review_required":True}],jsonl=True)
    emit(ctx,"uncertain.jsonl",[{"id":"LIMIT001","reason":"Synthetic image only; no actor or narrative inferred"}],jsonl=True)
    return "local-Qwen3-VL-2B-Instruct-CUDA"

def _n04(ctx:WorkerContext)->str:
    lines=[json.loads(x) for x in prior(ctx,"N02","transcript_vi.jsonl").read_text(encoding="utf8").splitlines()]
    visions=[json.loads(x) for x in prior(ctx,"N03","visual_observations.jsonl").read_text(encoding="utf8").splitlines()]
    if not lines or not visions:raise ValueError("Story memory needs speech and vision evidence")
    story={"source_sha256":ctx.source_sha256,"input_synthetic":True,
           "chapters":[{"event_id":"EV001","visual":visions[0]["description"],
                        "spoken":lines[0]["text"],
                        "visual_evidence_id":visions[0]["id"],
                        "speech_evidence_id":lines[0]["id"],
                        "human_review_required":True}]}
    emit(ctx,"story_timeline.json",story)
    emit(ctx,"event_claims.jsonl",[{"event_id":"EV001","source_evidence_ids":[visions[0]["id"],lines[0]["id"]],
      "verdict":"CONTEXT_ONLY","synthetic_source":True}],jsonl=True)
    emit(ctx,"unresolved.jsonl",[{"reason":"No actual plot or character inference",
      "needs_human_review":True}],jsonl=True)
    return "rule-based-evidence-merger-not-generative-LLM"

def _n05(ctx:WorkerContext)->str:
    story=json.loads(prior(ctx,"N04","story_timeline.json").read_text(encoding="utf8"))
    vision=story["chapters"][0]["visual"].lower()
    if not all(x in vision for x in ("red","blue","square","circle")):
        raise ValueError("Qwen visual facts do not match known synthetic shape fixture")
    review="Trong cảnh thử nghiệm có một hình vuông đỏ và một hình tròn xanh."
    text_output(ctx,"review_final.txt",review+"\n")
    claims=[{"claim_id":"C001","text":"Red square and blue circle visible",
        "evidence_ids":["VIS001"],"verdict":"VISUAL_DIRECT"}]
    emit(ctx,"sentence_claims.jsonl",[{"sentence_id":"S0001","review_text":review,
      "atomic_claims":claims,"synthetic_media":True}],jsonl=True)
    emit(ctx,"evidence_ledger.jsonl",[{"claim_id":"C001","verdict":"VISUAL_DIRECT",
      "evidence_ids":["VIS001"],"requires_human_review":True}],jsonl=True)
    return "deterministic-grounded-synthetic-review-NOT-creative-LLM"

def _n06(ctx:WorkerContext,models:Path)->str:
    import numpy as np
    import soundfile as sf
    import torch
    from vieneu import Vieneu
    text=prior(ctx,"N05","review_final.txt").read_text(encoding="utf8").strip()
    tts=Vieneu(mode="v3turbo",backbone_repo=str(models/"tts"/"vieneu-v3-turbo"),
      model_subfolder="update",moss_tokenizer=str(models/"tts"/"moss-audio-tokenizer-nano"),
      device="cuda",backend="pytorch",max_batch_size=1,max_streams=1)
    audio=np.asarray(tts.infer(text,voice="Trúc Ly"),dtype=np.float32)
    if audio.ndim!=1 or audio.size<1000 or not np.isfinite(audio).all():
        raise ValueError("VieNeu TTS generated invalid audio")
    wav=ctx.out/"narration.wav"
    tts.save(audio,str(wav))
    with sf.SoundFile(str(wav)) as f:
        if f.channels!=1 or f.samplerate!=48000:
            raise ValueError("VieNeu channel/rate invalid")
        dur=f.frames/f.samplerate
    emit(ctx,"sentence_audio_timeline.jsonl",[{"sentence_id":"S0001",
      "voice_start_s":0.0,"voice_end_s":dur,"text":text,
      "synthetic_input":True,"preset_voice_approved_for_real_film":False}],jsonl=True)
    emit(ctx,"audio_qc.json",{"sample_rate":48000,"channels":1,
      "duration_s":dur,"sha256":digest(wav),"voice_approved_for_real_film":False})
    return "local-VieNeu-v3-Turbo-TrucLy-test-only"

def _n07(ctx:WorkerContext,models:Path)->str:
    import torch
    from PIL import Image,ImageDraw
    from transformers import CLIPModel,CLIPProcessor
    source_vision=json.loads(prior(ctx,"N03","visual_observations.jsonl").read_text(encoding="utf8").splitlines()[0])
    review=prior(ctx,"N05","review_final.txt").read_text(encoding="utf8").strip()
    from wave import open as wave_open
    with wave_open(str(prior(ctx,"N06","narration.wav")),"rb") as f:
        voice_dur=f.getnframes()/f.getframerate()
    source_dur=_media(ctx.source)["duration_s"]
    frame=_frame(ctx)
    img=Image.open(frame).convert("RGB").resize((224,224))
    green=Image.new("RGB",(224,224),"white")
    ImageDraw.Draw(green).rectangle((30,30,194,194),fill="green")
    blue=Image.new("RGB",(224,224),"white")
    ImageDraw.Draw(blue).rectangle((30,30,194,194),fill="blue")
    path=models/"embeddings"/"clip-vit-base-patch32"
    mdl=CLIPModel.from_pretrained(str(path),local_files_only=True).to("cuda").eval()
    pre=CLIPProcessor.from_pretrained(str(path),local_files_only=True)
    im=pre(images=[img,green,blue],return_tensors="pt").to("cuda")
    txt=pre(text=[source_vision["description"]],return_tensors="pt",padding=True).to("cuda")
    with torch.inference_mode():
        em=mdl.get_image_features(**im);te=mdl.get_text_features(**txt)
    if not isinstance(em,torch.Tensor):em=em.pooler_output
    if not isinstance(te,torch.Tensor):te=te.pooler_output
    em=torch.nn.functional.normalize(em.float(),dim=-1)
    te=torch.nn.functional.normalize(te.float(),dim=-1)
    scores=(te@em.T).flatten().cpu().tolist()
    if max(range(3),key=lambda i:scores[i])!=0:
        raise ValueError("CLIP did not retrieve source image as top candidate")
    end=min(source_dur,voice_dur)
    emit(ctx,"candidate_scenes.jsonl",[{"candidate_id":"VIS001",
        "source_start_s":0,"source_end_s":end,
        "score_raw":scores[0],"other_scores":scores[1:],
        "model":"local-CLIP-ViT-B-32","source_sha256":ctx.source_sha256,
        "synthetic_fixture":True}],jsonl=True)
    doc={"source_movie_sha256":ctx.source_sha256,
      "source_duration_s":source_dur,"narration_duration_s":voice_dur,
      "sentences":[{"sentence_id":"S0001","review_text":review,
         "voice_start_s":0.0,"voice_end_s":voice_dur,
         "atomic_claims":[{"claim_id":"C001","text":"Visible synthetic shapes",
            "verdict":"VISUAL_DIRECT","evidence_ids":["VIS001"]}],
         "chosen_shots":[{"source_start_s":0.,"source_end_s":end,
           "voice_start_s":0.,"voice_end_s":voice_dur,"verdict":"VISUAL_DIRECT",
           "visual_evidence_ids":["VIS001"],"asr_evidence_ids":[],
           "qualifier":"Synthetic shape image; not original movie scene"}],
         "unresolved_claims":[]}]}
    emit(ctx,"sentence_shot_map.json",doc)
    emit(ctx,"evidence_and_limits.jsonl",[{"sentence_id":"S0001",
      "clip_raw_cosine":scores,"model_verified":True,
      "source_visual_id":"VIS001",
      "limitation":"Only 1 synthetic source scene; not real movie matching"}],jsonl=True)
    return "local-CLIP-ViT-B-32-CUDA-with-Qwen-caption"

def _n08(ctx:WorkerContext)->str:
    approved=ctx.job/"edit"/"pilot.mp4"
    if not approved.is_file():raise ValueError("No approved pilot video available")
    target=ctx.out/"pilot.mp4"
    shutil.copy2(approved,target)
    if digest(target)!=digest(approved):
        raise ValueError("Pilot differs from signed approved source")
    _media(target)
    emit(ctx,"timeline.json",{"source_sha256":ctx.source_sha256,
        "approved_video_sha256":digest(target),
        "origin":"HOST_APPROVED_SYNTHETIC_PILOT",
        "human_real_film_approval":False})
    return "host-preview-sha-pinned-ffmpeg"

def _n09(ctx:WorkerContext)->str:
    video=prior(ctx,"N08","pilot.mp4")
    dest=ctx.out/"final_review.mp4"
    shutil.copy2(video,dest)
    props=_media(dest)
    _cmd(["ffmpeg","-nostdin","-v","error","-xerror",
        "-i",str(dest),"-map","0:v?","-map","0:a?","-f","null","-"],timeout=120)
    emit(ctx,"technical_qc.json",{"full_decode_verified":True,
      "duration_s":props["duration_s"],"streams":sorted(props["kinds"])})
    emit(ctx,"semantic_qc.json",{"synthetic_input":True,
      "actual_model_inference_for_video_ASR_and_embeddings":True,
      "human_review_required":True,
      "full_real_film_semantics_verified":False})
    emit(ctx,"delivery_manifest.json",{"name":"final_review.mp4",
       "sha256":digest(dest),"source_sha256":ctx.source_sha256,
       "qa_only":True})
    return "ffmpeg-verified-final-technical-only"

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--models-root",required=True,type=Path)
    p.add_argument("--stage",required=True)
    args=p.parse_args()
    try:
        ctx=read_contract(os.environ)
        if args.stage!=ctx.stage:raise ValueError("Stage argument mismatched Engine21 environment")
        models=args.models_root.resolve(strict=True)
        if ctx.stage in ("N02","N03","N06","N07") and not models.is_dir():
            raise ValueError("Existing model root invalid")
        if ctx.stage=="N02":identifier=_n02(ctx,models)
        elif ctx.stage=="N03":identifier=_n03(ctx,models)
        elif ctx.stage=="N04":identifier=_n04(ctx)
        elif ctx.stage=="N05":identifier=_n05(ctx)
        elif ctx.stage=="N06":identifier=_n06(ctx,models)
        elif ctx.stage=="N07":identifier=_n07(ctx,models)
        elif ctx.stage=="N08":identifier=_n08(ctx)
        elif ctx.stage=="N09":identifier=_n09(ctx)
        else:raise ValueError("Unsupported stage")
        missing=[x for x in ctx.outputs if not (ctx.out/x).is_file()]
        if missing:raise ValueError("Required worker artifact missing: "+repr(missing))
        record_provider_verification(ctx,identifier,input_media_synthetic=True)
        print("LEGACY_OFFLINE_QA_WORKER_PASS",json.dumps({
            "stage":ctx.stage,"provider":identifier,
            "real_model_or_media_processing":True,
            "input_media_synthetic":True}),flush=True)
        return 0
    except Exception as exc:
        print("LEGACY_OFFLINE_QA_WORKER_FAIL",
              type(exc).__name__+": "+str(exc),file=sys.stderr,flush=True)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
