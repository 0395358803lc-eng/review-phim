"""Passive read-only capability inventory. No model inference or downloads."""
from __future__ import annotations
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

MODULES={
 "whisper":["faster_whisper","whisper"],
 "openclip":["open_clip"],
 "qwen3vl":["transformers","torch","qwen_vl_utils"],
 "vieneu":["vieneu","torch"],
 "scene_detection":["scenedetect"],
}
def installed()->dict:
    modules={name:{pkg:bool(importlib.util.find_spec(pkg)) for pkg in names}
             for name,names in MODULES.items()}
    media={key:shutil.which(key) for key in ("ffmpeg","ffprobe","git","nvidia-smi")}
    gpu={"available":False,"name":None,"memory_total_mib":None}
    if media["nvidia-smi"]:
        try:
            proc=subprocess.run([media["nvidia-smi"],"--query-gpu=name,memory.total",
                  "--format=csv,noheader,nounits"],stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE,text=True,timeout=10)
            if proc.returncode==0 and proc.stdout.strip():
                left,right=proc.stdout.splitlines()[0].rsplit(",",1)
                gpu={"available":True,"name":left.strip(),
                     "memory_total_mib":int(right.strip())}
        except (OSError,ValueError,subprocess.TimeoutExpired):
            pass
    return {"checked_at_utc":datetime.now(timezone.utc).isoformat(),
      "python":sys.version.split()[0],"python_executable":sys.executable,
      "modules":modules,"executables":media,"gpu":gpu,
      "notes":["Installed module is not proof model weights are cached or configured",
               "Unknown provider workers must be verified explicitly",
               "No software was installed or downloaded"]}

if __name__=="__main__":
    print(json.dumps(installed(),ensure_ascii=False,indent=2))
