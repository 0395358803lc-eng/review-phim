"""Validate independent real-model reports and render a synthetic evidence-linked review.

This is technical QA on generated shapes and narration, NOT real-film semantic proof.
No model weights are downloaded or written, and no legacy project files are changed.
"""
from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unicodedata
import wave

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))
sys.path.insert(0,str(REPO/"skills"/"film-review-orchestrator"/"scripts"))
from stage3.media import decode, probe, render
from stage3.framework import sha256
import evidence_qc

def _norm(value:str)->str:
    return " ".join(unicodedata.normalize("NFKC",value).lower().split())

def verify_model_reports(qwen_path:Path, clip_doc:dict, tts_doc:dict,
                         asr_doc:dict, voice_wav:Path)->dict:
    qwen_path=Path(qwen_path).resolve(strict=True)
    qwen=json.loads(qwen_path.read_text(encoding="utf8"))
    answer=qwen.get("generated_text")
    if qwen.get("status")!="PASS" or not isinstance(answer,str) or not answer.strip():
        raise ValueError("Qwen response missing or not successful")
    expected=sha256(qwen_path)
    if clip_doc.get("status")!="PASS" or clip_doc.get("qwen_report_sha256")!=expected:
        raise ValueError("Qwen caption and CLIP report are not the same source")
    if not clip_doc.get("query_texts") or clip_doc["query_texts"][0]!=answer:
        raise ValueError("Qwen visual caption changed before CLIP retrieval")
    if clip_doc.get("clip_embedding_dim")!=512:
        raise ValueError("CLIP embedding dimension unexpected")
    ranks=clip_doc.get("ranks")
    if (not isinstance(ranks,list) or not ranks or not ranks[0]
        or ranks[0][0]!="QWEN_SOURCE_FRAME" or clip_doc.get("correct_source_rank")!=1):
        raise ValueError("CLIP failed source-frame retrieval")
    digest=sha256(Path(voice_wav).resolve(strict=True))
    if tts_doc.get("status")!="PASS" or asr_doc.get("status")!="PASS":
        raise ValueError("One speech model failed")
    if tts_doc.get("wav_sha256")!=digest or asr_doc.get("wav_sha256")!=digest:
        raise ValueError("Voice WAV SHA mismatch between TTS and ASR")
    text=tts_doc.get("source_text")
    segments=asr_doc.get("segments")
    if not isinstance(text,str) or not text.strip() or not isinstance(segments,list) or not segments:
        raise ValueError("Voice script or speech segments missing")
    transcript=" ".join(str(x.get("text","")) for x in segments)
    similarity=SequenceMatcher(None,_norm(text),_norm(transcript)).ratio()
    if similarity<0.72:
        raise ValueError("Generated narration and recognized speech disagree")
    return {
      "source_frame_rank":1,
      "speech_similarity":round(similarity,4),
      "qwen_caption":answer,
      "review_text":text,
      "recognized_voice":transcript,
      "voice_sha256":digest,
      "qwen_report_sha256":expected,
      "clip_report_provenance":clip_doc.get("clip_model"),
      "synthetic_fixture":True,
      "warnings":["Review sentence written for a synthetic geometric drawing",
         "Narration ASR is not original film dialogue",
         "Model similarity on synthetic imagery is not validated on real film"],
    }

def _call_ffmpeg(image:Path,wav:Path,target:Path,seconds:float):
    command=["ffmpeg","-nostdin","-v","error","-loop","1","-framerate","24",
             "-i",str(image),"-i",str(wav),"-t",str(seconds),
             "-map","0:v:0","-map","1:a:0","-c:v","mpeg4","-q:v","4",
             "-pix_fmt","yuv420p","-c:a","aac","-movflags","+faststart",
             "-y",str(target)]
    p=subprocess.run(command,capture_output=True,timeout=120)
    if p.returncode:
        raise ValueError("Synthetic video generation failed: "+p.stderr.decode("utf8","replace")[-500:])

def run(args)->dict:
    source_image=Path(args.source_image).resolve(strict=True)
    voice=Path(args.voice_wav).resolve(strict=True)
    if not source_image.is_file() or not voice.is_file():
        raise ValueError("Synthetic source image or WAV not found")
    qwen=Path(args.qwen_report).resolve(strict=True)
    clip=json.loads(Path(args.clip_report).read_text(encoding="utf8"))
    tts=json.loads(Path(args.tts_report).read_text(encoding="utf8"))
    asr=json.loads(Path(args.asr_report).read_text(encoding="utf8"))
    linked=verify_model_reports(qwen,clip,tts,asr,voice)
    with wave.open(str(voice),"rb") as f:
        if f.getnchannels()!=1 or f.getframerate()!=48000:
            raise ValueError("Unexpected real TTS WAV channel/sample rate")
        seconds=f.getnframes()/f.getframerate()
    if not 0.4<seconds<30:
        raise ValueError("Unexpected narration duration for small QA clip")
    out=Path(args.output_dir)
    if out.exists():raise FileExistsError("Separate QA version required; no overwrites")
    out.mkdir(parents=True)
    frame=out/"source_synthetic_shapes.mp4"
    _call_ffmpeg(source_image,voice,frame,seconds)
    frame_stats=decode(frame,need_audio=True,need_video=True)
    filmhash=sha256(frame)
    voice_dur=probe(voice)["duration_s"]
    shot_dur=min(frame_stats["duration_s"],voice_dur)
    evidence_ids=["QWEN_VIS_001","CLIP_RANK_001"]
    review_sentence=linked["review_text"]
    doc={"source_movie_sha256":filmhash,
         "source_duration_s":frame_stats["duration_s"],
         "narration_duration_s":voice_dur,
         "synthetic_fixture":True,
         "sentences":[{
            "sentence_id":"S0001","review_text":review_sentence,
            "voice_start_s":0.,"voice_end_s":voice_dur,
            "atomic_claims":[{"claim_id":"VIS001",
               "text":"Synthetic red square and blue circle visible in source frame",
               "verdict":"VISUAL_DIRECT","evidence_ids":evidence_ids}],
            "chosen_shots":[{"source_start_s":0.,"source_end_s":shot_dur,
               "voice_start_s":0.,"voice_end_s":voice_dur,
               "verdict":"VISUAL_DIRECT",
               "visual_evidence_ids":evidence_ids,"asr_evidence_ids":[],
               "qualifier":"Synthetic model QA; not a real-film scene"}],
            "unresolved_claims":[]}]} 
    failures=evidence_qc.validate_map(doc)
    if failures:raise ValueError("Stage3 semantic evidence map rejected: "+";".join(failures))
    movie=out/"review_final.mp4"
    final_stats=render(frame,voice,movie,seconds)
    story={
      "synthetic_fixture":True,
      "source_sha256":filmhash,
      "events":[{"id":"EV_VIS_001",
                 "event":"Red square and blue circle appear together in generated still",
                 "time_s":[0,shot_dur],
                 "evidence_ids":evidence_ids,
                 "source":"real Qwen3-VL caption and real CLIP source-frame retrieval"}],
      "narration":{"origin":"VieNeu generated QA voice, not source movie dialogue",
                    "tts_voice_approved_for_production":False,
                    "wav_sha256":linked["voice_sha256"],
                    "asr_text":linked["recognized_voice"],
                    "recognition_similarity":linked["speech_similarity"]},
      "human_semantic_review_required":True}
    (out/"review_final.txt").write_text(review_sentence+"\n",encoding="utf8")
    (out/"story_memory.json").write_text(json.dumps(story,ensure_ascii=False,indent=2),encoding="utf8")
    (out/"sentence_shot_map.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf8")
    manifest={"status":"PASS","kind":"real_local_models_plus_synthetic_media",
       "source_sha256":filmhash,
       "source_image_sha256":sha256(source_image),
       "input_proof_sha256":{
         "qwen":sha256(qwen),"clip":sha256(Path(args.clip_report)),
         "tts":sha256(Path(args.tts_report)),"asr":sha256(Path(args.asr_report))},
       "story_review_grounded_by_source":True,
       "narration_asr_similarity":linked["speech_similarity"],
       "clip_source_frame_rank":linked["source_frame_rank"],
       "source_video_duration_s":frame_stats["duration_s"],
       "final_video_duration_s":final_stats["duration_s"],
       "final_video_sha256":sha256(movie),
       "final_video_bytes":movie.stat().st_size,
       "final_streams":final_stats["stream_types"],
       "limitations":linked["warnings"],
       "cannot_certify_full_movie":True}
    (out/"acceptance.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
    return manifest

def main():
    p=argparse.ArgumentParser()
    for arg in ("qwen-report","clip-report","tts-report","asr-report",
                "source-image","voice-wav","output-dir"):
        p.add_argument("--"+arg,type=Path,required=True)
    args=p.parse_args()
    result=run(args)
    print("LINKED_REAL_MODEL_SYNTHETIC_ACCEPTANCE_PASS",json.dumps(result,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
