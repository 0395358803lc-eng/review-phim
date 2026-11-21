"""Offline Phase6 REAL FILM workbench — user-authorized media stays local.

Usage:
  python -B qa/phase6_workbench.py --repo REPO --source MOVIE.mp4
    --source-sha256 PINNED_SHA --prior-qa OLDQA --phase5-qa PHASE5QA
    --out NEW_EMPTY_PRIVATE_OUTPUT

No package installs/downloads and no trusted human signature is produced.
Outputs (WAV, video URLs, original dialog, translations) are PRIVATE only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

def sha(path:Path)->str:
    hash_=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            hash_.update(block)
    return hash_.hexdigest()

def read_json(path:Path):
    return json.loads(path.read_text(encoding="utf8"))

def read_jsonl(path:Path):
    return [json.loads(x) for x in path.read_text(encoding="utf8").splitlines() if x.strip()]

def run(argv,timeout=180):
    p=subprocess.run(argv,stdin=subprocess.DEVNULL,capture_output=True,timeout=timeout)
    if p.returncode!=0:
        raise RuntimeError("Media command failure: "+p.stderr.decode("utf8","replace")[-450:])
    return p

def save(path:Path,data):
    with path.open("x",encoding="utf8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def ffmpeg_cuts(clip:Path,duration:float,threshold:float=.27)->list[float]:
    cmd=["ffmpeg","-nostdin","-hide_banner","-i",str(clip),
        "-vf",f"select='gt(scene,{threshold})',showinfo",
        "-an","-f","null","-"]
    p=run(cmd,timeout=180)
    stderr=p.stderr.decode("utf8","replace")
    all_times=[float(x) for x in re.findall(r"\bpts_time:([0-9]+(?:\.[0-9]+)?)",stderr)]
    selected=[]
    for t in all_times:
        if .15<t<duration-.15 and (not selected or t-selected[-1]>.15):
            selected.append(round(t,3))
    return selected

def extract_audio(movie:Path,rows:list[dict],out:Path)->list[dict]:
    audio_dir=out/"media"/"audio"
    audio_dir.mkdir(parents=True,exist_ok=False)
    manifest=[]
    for row in rows:
        id=row["id"]
        path=audio_dir/(id+".wav")
        start=float(row["preview_start_s"])
        end=float(row["preview_end_s"])
        dur=end-start
        if dur<=0 or dur>40:
            raise ValueError("Invalid bounded audio preview")
        run(["ffmpeg","-nostdin","-v","error",
             "-ss",f"{start:.3f}","-t",f"{dur:.3f}",
             "-i",str(movie),"-vn","-ac","1","-ar","16000",
             "-c:a","pcm_s16le","-n",str(path)],timeout=120)
        if not path.is_file() or path.stat().st_size<150:
            raise ValueError("Missing actual original audio sample")
        p=run(["ffprobe","-v","error","-show_format","-show_streams",
               "-of","json",str(path)],timeout=35)
        probe=json.loads(p.stdout.decode("utf8"))
        codecs=[s.get("codec_type") for s in probe.get("streams",[])]
        if "audio" not in codecs:
            raise ValueError("Original English speech audio extract has no audio")
        seconds=float(probe["format"]["duration"])
        if not .05<seconds<=dur+.1:
            raise ValueError("Decoded audio preview violates original sample bounds")
        manifest.append({"id":id,"source_sha256":row["source_sha256"],
                         "original_start_s":start,"original_end_s":end,
                         "preview_bytes":path.stat().st_size,
                         "audio_sha256":sha(path),"decoded_audio_s":round(seconds,3),
                         "relative_file":f"media/audio/{id}.wav",
                         "user_data_private":True})
    return manifest

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--repo",required=True,type=Path)
    a.add_argument("--source",required=True,type=Path)
    a.add_argument("--source-sha256",required=True)
    a.add_argument("--prior-qa",required=True,type=Path)
    a.add_argument("--phase5-qa",required=True,type=Path)
    a.add_argument("--out",required=True,type=Path)
    args=a.parse_args()
    root=args.repo.resolve(strict=True)
    movie=args.source.resolve(strict=True)
    prior=args.prior_qa.resolve(strict=True)
    p5=args.phase5_qa.resolve(strict=True)
    out=args.out.resolve(strict=True)
    # The new output must have no preexisting generated media to overwrite.
    if any(out.iterdir()):
        raise ValueError("Private Phase6 output must be an EMPTY directory")
    if movie.is_relative_to(out) or out.is_relative_to(prior) or out.is_relative_to(p5):
        raise ValueError("Old inputs and isolated output paths overlap")
    sys.path.insert(0,str(root))
    from stage6.dialogue_review import build_dialogue_review_queue
    from stage6.scene_proposals import build_scene_proposals
    from stage6.review_packet import build_review_packet
    from stage6.offline_html import render_review_html
    if sha(movie)!=args.source_sha256:
        raise ValueError("Original movie sha256 does not match authorized source")
    original=read_json(prior/"evidence"/"source_samples.json")
    raw_asr=read_jsonl(prior/"evidence"/"transcript_en.jsonl")
    translation=read_json(p5/"evidence"/"fatman_translation_unapproved.json")
    storyboard=read_json(p5/"evidence"/"fatman_three_sentence_storyboard_unapproved.json")
    source_catalog=read_json(prior/"reports"/"story_timeline_real_film.json")
    duration=float(original["original_duration_s"])
    if original.get("source_sha256")!=args.source_sha256 or abs(duration-storyboard["original_film_duration_s"])>.001:
        raise ValueError("Original film/source duration not consistent across previous phases")
    windows=original["windows"]
    queue=build_dialogue_review_queue(translation,raw_asr,args.source_sha256,duration,windows)
    cuts={}
    clips={}
    frames={}
    for w in windows:
        sample=w["sample_id"]
        clip=(prior/w["clip_path"]).resolve(strict=True)
        if not clip.is_file() or sha(clip)!=w["clip_sha256"]:
            raise ValueError("Read-only QA clip SHA differs: "+sample)
        clips[sample]=clip.as_uri()
        cuts[sample]=ffmpeg_cuts(clip,float(w["clip_duration_s"]))
        print("PRIVATE_PHASE6_CUTS",sample,len(cuts[sample]),flush=True)
        for frm in w["frames"]:
            path=(prior/frm["path"]).resolve(strict=True)
            if sha(path)!=frm["sha256"]:
                raise ValueError("Read-only frame SHA changed")
            frames["V_"+frm["frame_id"]]=path.as_uri()
    proposed=build_scene_proposals(args.source_sha256,duration,windows,cuts)
    pack=build_review_packet(args.source_sha256,storyboard,
                             source_catalog["catalog"],proposed,queue)
    previews=extract_audio(movie,queue["rows"],out)
    (out/"reports").mkdir(exist_ok=False)
    save(out/"reports"/"english_vi_dialogue_review_pending.json",queue)
    save(out/"reports"/"original_scene_boundaries_unapproved.json",proposed)
    save(out/"reports"/"real_film_review_packet_unsigned.json",pack)
    save(out/"reports"/"original_audio_preview_manifest.json",previews)
    with (out/"reports"/"fatman_offline_review_UNAPPROVED.html").open("x",encoding="utf8") as f:
        f.write(render_review_html(queue,pack,clips,frames))
    summary={"status":"LOCAL_QA_READY_PENDING_HUMAN_REVIEW",
       "film_source_sha256":args.source_sha256,
       "film_total_seconds":duration,
       "sample_source_window_count":len(windows),
       "sample_total_seconds":sum(w["original_end_s"]-w["original_start_s"] for w in windows),
       "asr_original_rows":len(raw_asr),"audio_preview_files":len(previews),
       "low_confidence_asr_needing_listen":queue["low_asr_count"],
       "suspected_translation_false_friend_count":queue["translation_warning_count"],
       "auto_cutpoint_total":proposed["auto_detected_cuts"],
       "auto_scene_candidate_count":len(proposed["scenes"]),
       "original_review_claims_count":len(pack["visual_claims"]),
       "original_review_claim_ids":[r["claim_id"] for r in pack["visual_claims"]],
       "visual_claims_human_approved":0,"translations_human_approved":0,
       "source_film_sha256_unchanged":False,
       "html_review_local_private":True,
       "audio_previews_private":True,
       "eligible_for_production_voice":False,"eligible_for_real_film_pilot":False,
       "signed_user_approvals_created":0,
       "limitations":["Scene cuts inferred from FFmpeg within only three short film excerpts",
                      "Human reviewer must listen to 17 WAV excerpts and inspect all 3 movie source clips",
                      "A pending reviewer worksheet cannot certify movie semantics or approve TTS/pilot"]}
    if sha(movie)!=args.source_sha256:
        raise ValueError("Original movie changed during private QA")
    summary["source_film_sha256_unchanged"]=True
    save(out/"reports"/"phase6_private_qa_summary.json",summary)
    print("PHASE6_REAL_FILM_PRIVATE_REVIEW_QUEUE",json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=="__main__":
    main()
