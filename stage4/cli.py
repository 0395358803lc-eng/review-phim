"""Portable Agent Skills CLI: evidence-first drafts and unsigned approval requests.

No external models installed or called here; host signs actual approvals separately.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .evidence import build_timeline
from .review import build_review
from .approval_requests import make_request,save_request

def _jsonl(path:Path)->list[dict]:
    file=Path(path).resolve(strict=True)
    if not file.is_file():raise ValueError("Evidence JSONL path is not file")
    rows=[]
    for no,line in enumerate(file.read_text(encoding="utf8").splitlines(),1):
        if not line.strip():continue
        row=json.loads(line)
        if not isinstance(row,dict):raise ValueError("Invalid JSONL evidence row "+str(no))
        rows.append(row)
    return rows

def _write_jsonl(out:Path,records:list[dict]):
    with out.open("x",encoding="utf8") as f:
        for row in records:
            f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")

def main(argv=None)->int:
    parser=argparse.ArgumentParser(description="Evidence-grounded movie review draft (not a real-film truth oracle)")
    sub=parser.add_subparsers(dest="task",required=True)
    draft=sub.add_parser("draft",help="Create source-grounded review DRAFT, never signed/final")
    draft.add_argument("--visual",type=Path,required=True)
    draft.add_argument("--asr",type=Path,required=True)
    draft.add_argument("--source-sha256",required=True)
    draft.add_argument("--source-duration",type=float,required=True)
    draft.add_argument("--output-dir",type=Path,required=True)
    draft.add_argument("--proposals",type=Path,help="Optional JSON array of model/author candidate claims")
    approval=sub.add_parser("approval-request",help="Create unsigned approval request under Engine21 job")
    approval.add_argument("--job",type=Path,required=True)
    approval.add_argument("--gate",choices=("script","voice","pilot"),required=True)
    args=parser.parse_args(argv)
    if args.task=="approval-request":
        result=make_request(args.job,args.gate)
        target=save_request(args.job,result)
        print("UNSIGNED_REQUEST_CREATED",target)
        return 0
    proposals=None
    if args.proposals:
        proposals=json.loads(Path(args.proposals).read_text(encoding="utf8"))
    story=build_timeline(_jsonl(args.asr),_jsonl(args.visual),
                         args.source_sha256,args.source_duration)
    review=build_review(story,proposals=proposals)
    out=Path(args.output_dir)
    if out.exists():raise FileExistsError("Output directory must be new: "+str(out))
    if not out.parent.is_dir():raise ValueError("Output parent directory unavailable")
    out.mkdir(exist_ok=False)
    (out/"story_timeline.json").write_text(json.dumps(story,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    with (out/"review_draft.txt").open("x",encoding="utf8") as f:
        f.write(review["review_text"]+"\n")
    _write_jsonl(out/"sentence_claims.jsonl",review["sentences"])
    _write_jsonl(out/"evidence_ledger.jsonl",review["evidence_ledger"])
    _write_jsonl(out/"unresolved.jsonl",story["unresolved"])
    _write_jsonl(out/"quarantined_proposals.jsonl",review["quarantined_proposals"])
    (out/"limitations.json").write_text(json.dumps({
        "human_approval_required":True,"approved_for_publication":False,
        "semantic_truth_certified":False,"limitations":review["limitations"],
        "source_sha256":story["source_sha256"]
    },ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("DRAFT_CREATED_UNAPPROVED",out,"SENTENCES",len(review["sentences"]))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
