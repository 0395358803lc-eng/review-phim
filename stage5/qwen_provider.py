"""Offline Qwen still-frame verifier used only behind Stage5 source controls.

Qwen model YES is not a human truth certificate, even if model loads on CUDA.
"""
from __future__ import annotations
from pathlib import Path
import re

def parse_visual_verdict(response:str)->str:
    if not isinstance(response,str):
        return "UNCERTAIN"
    match=re.fullmatch(r"\s*(YES|NO|UNCERTAIN)\s*[.!]?\s*",response,re.I)
    return match.group(1).upper() if match else "UNCERTAIN"

def ask_qwen_visual(frame:Path,claim_text:str,model_path:Path)->dict:
    if not isinstance(claim_text,str) or not claim_text.strip() or len(claim_text)>4000:
        raise ValueError("Cannot verify malformed visual claim")
    frame=Path(frame).resolve(strict=True)
    model_path=Path(model_path).resolve(strict=True)
    if not frame.is_file() or not (model_path/"model.safetensors").is_file():
        raise ValueError("Source still/model weights not available")
    import torch
    from PIL import Image
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    if not torch.cuda.is_available():
        raise RuntimeError("Offline Qwen GPU not available, refuse silent CPU fallback")
    pic=Image.open(frame).convert("RGB")
    proc=AutoProcessor.from_pretrained(str(model_path),local_files_only=True)
    model=Qwen3VLForConditionalGeneration.from_pretrained(
        str(model_path),torch_dtype=torch.bfloat16,attn_implementation="sdpa",
        device_map="auto",max_memory={0:"6GiB","cpu":"18GiB"},
        low_cpu_mem_usage=True,local_files_only=True).eval()
    prompt=("Check only THIS STILL IMAGE. Does EVERY factual visible detail of "
            "the following claim match what is actually seen? If a detail is "
            "absent, inferred from dialogue/plot, or not visually verifiable, "
            "answer NO or UNCERTAIN. Claim: "+claim_text+
            "\nRespond exactly one word: YES, NO or UNCERTAIN.")
    messages=[{"role":"user","content":[{"type":"image","image":pic},
                {"type":"text","text":prompt}]}]
    tokens=proc.apply_chat_template(messages,tokenize=True,
       add_generation_prompt=True,return_dict=True,return_tensors="pt").to(model.device)
    with torch.inference_mode():
        produced=model.generate(**tokens,max_new_tokens=12,do_sample=False)
    answer=proc.decode(produced[0,tokens["input_ids"].shape[1]:],
                       skip_special_tokens=True).strip()
    parsed=parse_visual_verdict(answer)
    return {"verdict":parsed,"raw_response":answer,
            "model_id":"Qwen3-VL-2B-Instruct-CUDA",
            "human_approved":False,"model_semantics_certified":False}
