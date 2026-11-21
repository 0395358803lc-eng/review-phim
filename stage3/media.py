"""Real FFmpeg media operations; available only with host-installed binaries."""
from __future__ import annotations
import json
from pathlib import Path
import re
import shutil
import subprocess


def _program(name:str)->str:
    executable=shutil.which(name)
    if not executable:
        raise RuntimeError("Installed "+name+" executable unavailable; no downloads")
    return executable


def _call(command:list[str], timeout:int=300, *,capture:bool=True)->subprocess.CompletedProcess:
    result=subprocess.run(command,stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE,timeout=timeout,check=False)
    if result.returncode:
        raise ValueError("Media command failed ("+str(result.returncode)+"): "+
                         result.stderr.decode("utf8","replace")[-500:])
    return result


def probe(path:Path)->dict:
    source=Path(path)
    if not source.is_file() or not source.stat().st_size:
        raise ValueError("Media source not readable")
    result=_call([_program("ffprobe"),"-v","error","-show_streams",
        "-show_format","-of","json",str(source)],timeout=90)
    doc=json.loads(result.stdout.decode("utf8"))
    streams=doc.get("streams",[])
    kinds=sorted({x.get("codec_type") for x in streams if x.get("codec_type")})
    duration=float(doc.get("format",{}).get("duration") or 0)
    if duration<=0 or not kinds:
        raise ValueError("Invalid duration or media streams")
    return {"duration_s":duration,"stream_types":kinds,
            "streams":[{"codec_type":s.get("codec_type"),
                         "codec_name":s.get("codec_name")} for s in streams],
            "bytes":source.stat().st_size}


def decode(path:Path,*,need_video:bool=False,need_audio:bool=False)->dict:
    p=probe(path)
    if need_video and "video" not in p["stream_types"]:
        raise ValueError("Missing required video stream")
    if need_audio and "audio" not in p["stream_types"]:
        raise ValueError("Missing required audio stream")
    _call([_program("ffmpeg"),"-nostdin","-v","error","-xerror","-i",str(path),
           "-map","0:v?","-map","0:a?","-f","null","-"],timeout=3600)
    return p


def scene_index(path:Path, duration_s:float,threshold:float=0.32)->tuple[list[dict],list[dict]]:
    """Detect real cuts using FFmpeg scene score; guaranteed coverage 0-duration."""
    if not 0<threshold<1 or duration_s<=0:
        raise ValueError("Scene threshold or duration invalid")
    proc=_call([_program("ffmpeg"),"-nostdin","-hide_banner","-v","info",
        "-i",str(path),"-vf",f"select='gt(scene,{threshold})',showinfo",
        "-an","-f","null","-"],timeout=3600)
    diagnostics=proc.stderr.decode("utf8","replace")
    raw=[float(s) for s in re.findall(r"pts_time:\s*([0-9]+(?:\.[0-9]+)?)",diagnostics)]
    cuts=sorted(set(round(x,4) for x in raw if 0.05<x<duration_s-0.05))
    boundaries=[0.,*cuts,float(duration_s)]
    scenes=[];frames=[]
    for i,(start,end) in enumerate(zip(boundaries,boundaries[1:]),1):
        if end<=start:continue
        sid=f"SC{i:06}"
        scenes.append({"scene_id":sid,"start_s":start,"end_s":end,
            "duration_s":round(end-start,4),"source_kind":"FFMPEG_SCENE_DETECT",
            "threshold":threshold})
        frames.append({"frame_id":f"FR{i:06}","scene_id":sid,
            "timestamp_s":round((start+end)/2,4),"extracted":False,
            "note":"Timestamp index only; Qwen worker must decode real frames"})
    if not scenes or abs(scenes[-1]["end_s"]-duration_s)>0.001:
        raise ValueError("Scene indexing did not cover full source duration")
    return scenes,frames


def synth_wav(path:Path,duration_s:float=0.8)->dict:
    _call([_program("ffmpeg"),"-nostdin","-v","error","-f","lavfi",
        "-i",f"sine=frequency=520:sample_rate=16000:duration={duration_s}",
        "-c:a","pcm_s16le","-y",str(path)],timeout=30)
    return decode(path,need_audio=True)


def render(video:Path, voice:Path, output:Path, duration_s:float)->dict:
    if duration_s<=0:
        raise ValueError("Render duration must be positive")
    decode(voice,need_audio=True)
    _call([_program("ffmpeg"),"-nostdin","-v","error",
         "-i",str(video),"-i",str(voice),"-map","0:v:0",
         "-map","1:a:0","-t",str(duration_s),"-c:v","mpeg4",
         "-q:v","5","-c:a","aac","-ar","16000","-movflags","+faststart",
         "-y",str(output)],timeout=600)
    return decode(output,need_video=True,need_audio=True)
