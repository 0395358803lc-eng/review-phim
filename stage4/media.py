"""Synthetic QA-only repeating video renders: preserve full real-TTS narration.

This is a TECHNICAL playback fixture, not a source-faithful creative edit.
Never use a repeated synthetic shot as proof that a real-film event occurred.
"""
from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
from stage3.media import probe,decode

def loop_source_with_voice(source_video:Path,voice_wav:Path,output_mp4:Path)->dict:
    source_video=Path(source_video).resolve(strict=True)
    voice_wav=Path(voice_wav).resolve(strict=True)
    output_mp4=Path(output_mp4)
    if output_mp4.exists():raise FileExistsError("Never overwrite preview/pilot")
    if not output_mp4.parent.is_dir():
        raise ValueError("Output directory missing")
    source=decode(source_video,need_video=True)
    voice=decode(voice_wav,need_audio=True)
    duration=voice["duration_s"]
    if not 0<duration<=600:
        raise ValueError("Invalid QA narration length")
    program=shutil.which("ffmpeg")
    if not program:raise RuntimeError("Installed FFmpeg required; no installation")
    argv=[program,"-nostdin","-v","error","-stream_loop","-1",
          "-i",str(source_video),"-i",str(voice_wav),
          "-map","0:v:0","-map","1:a:0","-t",str(duration),
          "-c:v","mpeg4","-q:v","5","-pix_fmt","yuv420p",
          "-c:a","aac","-movflags","+faststart","-n",str(output_mp4)]
    cp=subprocess.run(argv,stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                       timeout=600,check=False)
    if cp.returncode:
        raise RuntimeError("QA render failed: "+cp.stderr.decode("utf8","replace")[-400:])
    result=decode(output_mp4,need_video=True,need_audio=True)
    if abs(result["duration_s"]-duration)>0.11:
        raise ValueError("Rendered preview truncated the spoken audio")
    return {"synthetic_loop":True,"voice_duration_s":duration,
            "output_duration_s":result["duration_s"],
            "source_duration_s":source["duration_s"],
            "full_audio_video_decode_pass":True,
            "limitations":["QA repeats original image; no real-film montage semantics"]}
