"""Allowlisted optional local model workers. No install, network, shell or weight download."""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess
from .framework import sha256

PROVIDER_STAGES=("N02","N03","N04","N05","N06","N07","N08","N09")

def verify_provider_config(path:Path)->dict:
    path=Path(path).resolve(strict=True)
    doc=json.loads(path.read_text(encoding="utf8"))
    if doc.get("schema_version")!="3.0" or not isinstance(doc.get("stages"),dict):
        raise ValueError("Invalid local model provider config")
    for stage,spec in doc["stages"].items():
        if stage not in PROVIDER_STAGES or not isinstance(spec,dict):
            raise ValueError("Unexpected local model stage")
        executable=Path(str(spec.get("executable","")))
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError("Provider executable must be installed absolute file")
        if sha256(executable)!=spec.get("executable_sha256"):
            raise ValueError("Provider executable changed since approval")
        argv=spec.get("argv")
        if not isinstance(argv,list) or not argv or any(not isinstance(x,str) for x in argv):
            raise ValueError("Provider argv is required")
        timeout=spec.get("timeout_seconds")
        if type(timeout) is not int or not 1<=timeout<=3600:
            raise ValueError("Provider timeout must be 1-3600 seconds")
        files=spec.get("input_files",{})
        if not isinstance(files,dict) or not files:
            raise ValueError("Production worker must pin at least one approved script/model file")
        for filename,digest in files.items():
            p=Path(filename)
            if not p.is_absolute() or not p.is_file() or sha256(p)!=digest:
                raise ValueError("Provider worker or checkpoint hash changed")
        for arg in argv:
            if "\x00" in arg or re.search(r"\{(?!source\}|output_dir\}|job\}|stage\})[a-zA-Z_]+\}",arg):
                raise ValueError("Unknown provider command substitution")
    return doc

def run_host_provider(ctx, config_path:Path|None)->str:
    if config_path is None:
        raise RuntimeError("Production "+ctx.stage+" requires installed, authorized local model worker")
    config=verify_provider_config(config_path)
    spec=config["stages"].get(ctx.stage)
    if spec is None:
        raise RuntimeError("Provider unavailable for "+ctx.stage+"; no synthetic fallback")
    if Path(config_path).resolve().is_relative_to(ctx.job):
        raise ValueError("Trusted provider config must be outside the job")
    mapping={"source":str(ctx.source),"output_dir":str(ctx.output_dir),
             "job":str(ctx.job),"stage":ctx.stage}
    argv=[]
    for arg in spec["argv"]:
        for key,value in mapping.items():
            arg=arg.replace("{"+key+"}",value)
        argv.append(arg)
    command=[spec["executable"],*argv]
    p=subprocess.run(command,cwd=ctx.output_dir,stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     timeout=spec["timeout_seconds"],check=False)
    if p.returncode:
        raise RuntimeError("Local worker failed ("+str(p.returncode)+"): "+
                           p.stderr.decode("utf8","replace")[-500:])
    verification=ctx.output_dir/"provider_verification.json"
    if not verification.is_file():
        raise ValueError("Real model provider must write verified checks and model provenance")
    claimed=json.loads(verification.read_text(encoding="utf8"))
    if claimed.get("source_sha256")!=ctx.source_sha256 or claimed.get("stage")!=ctx.stage:
        raise ValueError("Provider response provenance mismatch")
    if not claimed.get("model_id") or claimed.get("synthetic_fixture") is not False:
        raise ValueError("Model checkpoint provenance absent or synthetic")
    if set(claimed.get("checks",{}))!=set(ctx.required_checks):
        raise ValueError("Provider did not report required checks")
    if any(claimed["checks"][x] is not True for x in ctx.required_checks):
        raise ValueError("Provider validation reports failed checks")
    for item in ctx.required_outputs:
        if not (ctx.output_dir/item).is_file():
            raise ValueError("Provider output missing: "+item)
    return str(claimed["model_id"])
