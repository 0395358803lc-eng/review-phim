"""N00-N09 output contract: fail closed, digest bound, append-only attempts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

def runtime_digest()->str:
    """Pin every runtime Python module, not only the adapter entry script."""
    root=Path(__file__).resolve().parents[1]
    files=[root/"stage3_adapter.py",*sorted((root/"stage3").glob("*.py"))]
    digest=hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf8")+b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()

def sha256(path:Path)->str:
    digest=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()

@dataclass(frozen=True)
class StageContext:
    job:Path
    stage:str
    output_dir:Path
    source:Path
    source_sha256:str
    required_outputs:tuple[str,...]
    required_checks:tuple[str,...]

    @classmethod
    def from_env(cls, environ:Mapping[str,str])->"StageContext":
        from engine21.state import REQUIRED_OUTPUTS,CHECKS
        stage=str(environ["FRA_STAGE"])
        if stage not in REQUIRED_OUTPUTS: raise ValueError("Invalid stage")
        try:
            job=Path(environ["FRA_JOB"]).resolve(strict=True)
            source=Path(environ["FRA_SOURCE"]).resolve(strict=True)
            output=Path(environ["FRA_OUTPUT_DIR"]).resolve(strict=True)
        except FileNotFoundError as exc:
            raise ValueError("Job, source or stage attempt path does not exist") from exc
        if not source.is_file() or sha256(source)!=environ["FRA_SOURCE_SHA256"]:
            raise ValueError("Source checksum mismatch")
        source_metadata=json.loads((job/"job_state.json").read_text(encoding="utf8"))["source"]
        if (Path(source_metadata["absolute_path"]).resolve(strict=True)!=source
            or source_metadata["sha256"]!=environ["FRA_SOURCE_SHA256"]):
            raise ValueError("Job manifest does not reference locked original source")
        target=(job/".engine21"/"attempts"/stage).resolve()
        if not output.is_relative_to(target) or output.parent!=target:
            raise ValueError("Output must be stage attempt directory inside job")
        if (job/".engine21").is_symlink():
            raise ValueError("Engine root may not be symlink")
        outputs=tuple(json.loads(environ["FRA_REQUIRED_OUTPUTS"]))
        checks=tuple(json.loads(environ["FRA_REQUIRED_CHECKS"]))
        if outputs!=REQUIRED_OUTPUTS[stage] or checks!=CHECKS[stage]:
            raise ValueError("Required stage artifact/check contract changed")
        return cls(job,stage,output,source,environ["FRA_SOURCE_SHA256"],outputs,checks)

    def write_text(self,name:str,value:str)->Path:
        if not isinstance(name,str) or not re.fullmatch(r"[a-zA-Z0-9._-]+",name):
            raise ValueError("Invalid artifact filename")
        p=self.output_dir/name
        if p.exists():raise FileExistsError("Artifact exists; never overwrite")
        p.write_text(value,encoding="utf8")
        return p

    def write_json(self,name:str,value:object)->Path:
        return self.write_text(name,json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n")

    def write_jsonl(self,name:str,rows:list[dict])->Path:
        return self.write_text(name,"".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in rows))

    def prior(self,stage:str,artifact:str)->Path:
        """Only read stage files already generated inside the same isolated job."""
        from engine21.state import REQUIRED_OUTPUTS
        if stage not in REQUIRED_OUTPUTS or artifact not in REQUIRED_OUTPUTS[stage]:
            raise ValueError("Untrusted upstream artifact request")
        attempts=self.job/".engine21"/"attempts"/stage
        if not attempts.is_dir():raise ValueError("Upstream stage missing: "+stage)
        paths=sorted(p for p in attempts.glob("*/"+artifact)
                     if p.is_file() and p.resolve().is_relative_to(self.job))
        if not paths:raise ValueError("Upstream artifact unavailable: "+stage+"/"+artifact)
        return paths[-1]

    def evidence(self,mode:str,*,limitations:list[str],provider:str)->dict:
        missing=[x for x in self.required_outputs if not (self.output_dir/x).is_file()]
        if missing:raise ValueError("Required outputs absent: "+repr(missing))
        artifacts=[]
        for filename in self.required_outputs:
            p=self.output_dir/filename
            if p.stat().st_size==0:raise ValueError("Artifact empty: "+filename)
            if p.suffix==".json":json.loads(p.read_text(encoding="utf8"))
            if p.suffix==".jsonl":
                for line in p.read_text(encoding="utf8").splitlines():
                    if line:json.loads(line)
            artifacts.append({"path":str(p.relative_to(self.job)),"sha256":sha256(p)})
        if sha256(self.source)!=self.source_sha256:
            raise ValueError("Original source changed during adapter execution")
        doc={"stage":self.stage,"outcome":"PASS","source_sha256":self.source_sha256,
          "reviewed_at_utc":datetime.now(timezone.utc).isoformat(),
          "checks":{x:True for x in self.required_checks},"artifacts":artifacts,
          "synthetic_fixture":mode=="synthetic","provider":provider,
          "limitations":limitations}
        self.write_json("evidence.json",doc)
        return doc

def run_stage(*,mode:str,environ:Mapping[str,str],provider_config:Path|None=None)->dict:
    if mode not in ("synthetic","production"):raise ValueError("Explicit mode required")
    ctx=StageContext.from_env(environ)
    from .pipeline import build_stage
    provider=build_stage(ctx,mode,provider_config)
    limits=(["SYNTHETIC_FIXTURE_ONLY; no real AI inference, speech or human approval",
             "Synthetic narrative and audio cannot certify content matching"] if mode=="synthetic"
            else ["Provider output content requires human semantic review",
                  "Do not infer that static evidence checks prove film correctness"])
    doc=ctx.evidence(mode,limitations=limits,provider=provider)
    return {"stage":ctx.stage,"mode":mode,"provider":provider,
            "synthetic_fixture":doc["synthetic_fixture"],
            "artifacts":doc["artifacts"]}
