"""Stage-specific verifiable artifacts. Synthetic fixtures are explicitly labeled."""
from __future__ import annotations
import json
from pathlib import Path
import shutil

from .framework import StageContext,sha256
from . import media,providers

REVIEW_FIXTURE="Đây là đoạn phim mẫu tổng hợp, không phản ánh nội dung của bất kỳ bộ phim thật nào."
CLAIM_FIXTURE={"claim_id":"C0001","text":"Synthetic test, no movie-world assertion",
    "verdict":"CONTEXT_ONLY","evidence_ids":[]}

def _synthetic(ctx:StageContext)->None:
    st=ctx.stage
    if st=="N02":
        line={"id":"ASR_SYNTH_001","start_s":0.0,"end_s":0.7,"text":"Lời thoại được mô phỏng cho kiểm thử, không phải ASR",
            "language":"vi","synthetic_fixture":True,"source_sha256":ctx.source_sha256}
        ctx.write_jsonl("transcript_original.jsonl",[line])
        ctx.write_jsonl("transcript_vi.jsonl",[dict(line,translation_kind="synthetic_placeholder")])
        ctx.write_jsonl("uncertainties.jsonl",[{"status":"NOT_TRANSCRIBED",
            "reason":"synthetic source has test tone, no speech recognition was run"}])
    elif st=="N03":
        d=media.probe(ctx.source)
        ctx.write_jsonl("visual_observations.jsonl",[{"id":"VIS_SYNTH_001",
            "start_s":0,"end_s":d["duration_s"],
            "description":"Synthetic single-color frame / generated QA fixture",
            "verified_by_model":False,"synthetic_fixture":True}])
        ctx.write_jsonl("uncertain.jsonl",[{"reason":"No Qwen3-VL used in synthetic test",
                                           "requires_human_review":True}])
    elif st=="N04":
        ctx.write_json("story_timeline.json",{"synthetic_fixture":True,
            "source_sha256":ctx.source_sha256,
            "chapters":[{"event_id":"EV_SYNTH_001","description":"Synthetic fixture only",
                         "source_evidence_ids":["ASR_SYNTH_001","VIS_SYNTH_001"]}]})
        ctx.write_jsonl("event_claims.jsonl",[{"event_id":"EV_SYNTH_001",
            "source_evidence_ids":["ASR_SYNTH_001","VIS_SYNTH_001"],
            "verdict":"CONTEXT_ONLY","synthetic_fixture":True}])
        ctx.write_jsonl("unresolved.jsonl",[{"id":"UNKNOWN_1","description":
            "No real film narrative inference performed"}])
    elif st=="N05":
        ctx.write_text("review_final.txt",REVIEW_FIXTURE+"\n")
        ctx.write_jsonl("sentence_claims.jsonl",[{"sentence_id":"S0001",
            "review_text":REVIEW_FIXTURE,"atomic_claims":[CLAIM_FIXTURE],
            "synthetic_fixture":True}])
        ctx.write_jsonl("evidence_ledger.jsonl",[{"claim_id":"C0001",
            "verdict":"CONTEXT_ONLY","evidence_ids":[],
            "qualifier":"No actual film dialogue or actor claims established"}])
    elif st=="N06":
        voice=ctx.output_dir/"narration.wav"
        p=media.synth_wav(voice,duration_s=0.8)
        length=p["duration_s"]
        ctx.write_jsonl("sentence_audio_timeline.jsonl",[{"sentence_id":"S0001",
          "voice_start_s":0.,"voice_end_s":length,
          "text":REVIEW_FIXTURE,"synthetic_fixture":True,
          "not_speech":True}])
        ctx.write_json("audio_qc.json",{"duration_s":length,"streams":p["streams"],
          "full_decode_verified":True,"synthetic_sine_not_TTS":True})
    elif st=="N07":
        source_length=media.probe(ctx.source)["duration_s"]
        voice_length=media.probe(ctx.prior("N06","narration.wav"))["duration_s"]
        end=min(source_length,voice_length)
        if end<0.05:raise ValueError("Synthetic source or voice too short")
        candidate={"candidate_id":"SYNTH_SCENE_001","source_start_s":0,
          "source_end_s":end,"semantic_score":None,"model_verified":False,
          "source_sha256":ctx.source_sha256,"synthetic_fixture":True}
        ctx.write_jsonl("candidate_scenes.jsonl",[candidate])
        ctx.write_json("sentence_shot_map.json",{
          "source_movie_sha256":ctx.source_sha256,
          "source_duration_s":source_length,"narration_duration_s":voice_length,
          "sentences":[{"sentence_id":"S0001","review_text":REVIEW_FIXTURE,
             "voice_start_s":0,"voice_end_s":voice_length,
             "atomic_claims":[CLAIM_FIXTURE],
             "chosen_shots":[{"source_start_s":0,"source_end_s":end,
               "voice_start_s":0,"voice_end_s":voice_length,
               "visual_evidence_ids":[],"asr_evidence_ids":[],
               "verdict":"CONTEXT_ONLY",
               "qualifier":"Synthetic demonstration, no CLIP/Qwen verification"}],
             "unresolved_claims":[]}],
             "synthetic_fixture":True})
        ctx.write_jsonl("evidence_and_limits.jsonl",[{
          "sentence_id":"S0001","classification":"CONTEXT_ONLY",
          "limits":["No actual semantic scene matching or model inference"]}])
    else:
        raise ValueError("No synthetic builder for stage "+st)

def _video_stage(ctx:StageContext,mode:str)->None:
    if ctx.stage=="N00":
        inspected=media.decode(ctx.source,need_video=True,need_audio=True)
        inspected.update({"source_sha256":ctx.source_sha256,
                          "verified_by":"installed FFmpeg/FFprobe",
                          "synthetic_fixture":mode=="synthetic"})
        ctx.write_json("source_manifest.json",inspected)
    elif ctx.stage=="N01":
        props=media.probe(ctx.source)
        scenes,frames=media.scene_index(ctx.source,props["duration_s"])
        ctx.write_jsonl("scenes.jsonl",scenes)
        ctx.write_jsonl("frames.jsonl",frames)
    elif ctx.stage=="N08":
        voice=ctx.prior("N06","narration.wav")
        duration=min(media.probe(ctx.source)["duration_s"],
                     media.probe(voice)["duration_s"])
        props=media.render(ctx.source,voice,ctx.output_dir/"pilot.mp4",duration)
        ctx.write_json("timeline.json",{"source_sha256":ctx.source_sha256,
            "voice_sha256":sha256(voice),"output_duration_s":props["duration_s"],
            "cut_strategy":"single synthetic/preview segment, no semantic editorial judgement"})
    elif ctx.stage=="N09":
        pilot=ctx.prior("N08","pilot.mp4")
        target=ctx.output_dir/"final_review.mp4"
        shutil.copy2(pilot,target)
        props=media.decode(target,need_video=True,need_audio=True)
        ctx.write_json("technical_qc.json",{"decode_passed":True,
            "media":props,"source_sha256":ctx.source_sha256})
        ctx.write_json("semantic_qc.json",{"semantic_verified":False,
            "human_review_required":True,
            "limits":["Synthetic QA only; no character/action/plot verification"]})
        ctx.write_json("delivery_manifest.json",{"file_name":"final_review.mp4",
            "sha256":sha256(target),"source_sha256":ctx.source_sha256,
            "synthetic_fixture":True})
    else:
        raise ValueError("Unknown deterministic video stage")

def build_stage(ctx:StageContext,mode:str,provider_config:Path|None)->str:
    stage=ctx.stage
    if stage in ("N00","N01") or (mode=="synthetic" and stage in ("N08","N09")):
        _video_stage(ctx,mode)
        return "installed-ffmpeg"
    if mode=="synthetic":
        _synthetic(ctx)
        return "SYNTHETIC_FIXTURE_NOT_REAL_MODEL"
    if stage in providers.PROVIDER_STAGES:
        provider=providers.run_host_provider(ctx,provider_config)
        if stage=="N08":
            approved=ctx.job/"edit"/"pilot.mp4"
            rendered=ctx.output_dir/"pilot.mp4"
            if not approved.is_file() or not rendered.is_file() or sha256(approved)!=sha256(rendered):
                raise ValueError("Produced pilot differs from the host-approved pilot media digest")
        return provider
    raise ValueError("Unsupported stage or mode")
