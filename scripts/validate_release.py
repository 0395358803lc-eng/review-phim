#!/usr/bin/env python3
"""Static, cross-runtime checks for standalone Agent Skills ZIP sources."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import re
import sys

EXPECTED = {
    "film-review-orchestrator", "film-intake", "scene-indexing", "speech-analysis",
    "visual-analysis", "story-memory", "review-writing", "voice-production",
    "semantic-matching", "video-editing", "quality-delivery",
}
BAD_MEDIA = {".mp4", ".mov", ".mkv", ".avi", ".mp3", ".wav", ".flac", ".npz", ".sqlite", ".pt", ".safetensors", ".onnx"}


def validate(root: Path) -> list[str]:
    problems = []
    skills_path = root / "skills"
    actual = {p.name for p in skills_path.iterdir() if p.is_dir()} if skills_path.is_dir() else set()
    if actual != EXPECTED:
        problems.append(f"Skill directories mismatch: extra={actual-EXPECTED}, missing={EXPECTED-actual}")
    for skill in sorted(EXPECTED):
        path = skills_path / skill / "SKILL.md"
        if not path.is_file():
            problems.append(f"Missing {path}")
            continue
        content = path.read_text(encoding="utf-8")
        front = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
        if not front:
            problems.append(f"{skill}: missing YAML frontmatter")
            continue
        meta = dict(re.findall(r"^(name|description):\s*(.*?)\s*$", front.group(1), re.MULTILINE))
        if meta.get("name") != skill or not meta.get("description", "").startswith("Use when "):
            problems.append(f"{skill}: malformed discovery metadata")
        if len(meta.get("description", "")) > 1024:
            problems.append(f"{skill}: description longer than 1024 chars")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill) or len(skill) > 64:
            problems.append(f"{skill}: invalid name")
        if len(content) > 28000:
            problems.append(f"{skill}: very large SKILL.md; move details to references")
        if not content.split("---\n", 2)[-1].strip():
            problems.append(f"{skill}: empty body")
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in BAD_MEDIA:
            problems.append(f"Packaged media or model: {path.relative_to(root)}")
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            problems.append(f"Unwanted runtime cache: {path.relative_to(root)}")
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                problems.append(f"Invalid JSON {path.relative_to(root)}: {exc}")
    for name in ("job-state.schema.json", "stage-evidence.schema.json", "sentence-shot-map.schema.json"):
        path = root / "skills/film-review-orchestrator/schemas" / name
        if not path.is_file():
            problems.append(f"Missing schema {name}")
    for name in ("jobctl.py", "evidence_qc.py"):
        path = root / "skills/film-review-orchestrator/scripts" / name
        if not path.is_file():
            problems.append(f"Missing runtime script {name}")
    # Test every explicit relative Markdown link; external URLs are intentionally not checked.
    for path in list(root.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", content):
            link = link.split("#", 1)[0]
            if not link or "://" in link or link.startswith("mailto:"):
                continue
            target = (path.parent / link).resolve()
            if not target.exists():
                problems.append(f"Broken relative link {path.relative_to(root)} -> {link}")
    if importlib.util.find_spec("jsonschema"):
        import jsonschema
        for name in ("job-state.schema.json", "stage-evidence.schema.json", "sentence-shot-map.schema.json"):
            schema = json.loads((root / "skills/film-review-orchestrator/schemas" / name).read_text(encoding="utf-8"))
            try:
                jsonschema.Draft202012Validator.check_schema(schema)
            except Exception as exc:
                problems.append(f"Malformed JSON schema {name}: {exc}")
        example = json.loads((root / "skills/film-review-orchestrator/templates/match-example.synthetic.json").read_text(encoding="utf-8"))
        schema = json.loads((root / "skills/film-review-orchestrator/schemas/sentence-shot-map.schema.json").read_text(encoding="utf-8"))
        try:
            jsonschema.validate(example, schema)
        except Exception as exc:
            problems.append(f"Synthetic match example does not validate: {exc}")
    return problems


def main(argv=None) -> int:
    root = Path((argv or sys.argv[1:])[0] if (argv or sys.argv[1:]) else Path(__file__).resolve().parents[1]).resolve()
    errors = validate(root)
    if errors:
        for e in errors:
            print("FAIL", e, file=sys.stderr)
        return 2
    print(f"PASS: {len(EXPECTED)} valid Agent Skills, standard runtime scripts, JSON schema, links and no packaged user media")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
