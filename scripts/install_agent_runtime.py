#!/usr/bin/env python3
"""Install only Film Review Agent Skills + importable runtime source.

No old film data, model checkpoints, synthetic fixtures, QA output, tests,
or sample media are ever copied. A prior installation is never overwritten.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

SKILLS = (
    "film-review-orchestrator", "film-intake", "scene-indexing",
    "speech-analysis", "visual-analysis", "story-memory",
    "review-writing", "voice-production", "semantic-matching",
    "video-editing", "quality-delivery",
)
RUNTIME_PACKAGES = ("engine21", "stage3", "stage4", "stage5", "stage6")
ROOT = Path(__file__).resolve().parents[1]
SCRIPT_FILES = (
    "stage3_adapter.py",
    "qa/phase6_workbench.py",
    "AGENT_RUNTIME.md",
    "examples/engine21-adapters.example.json",
    "examples/phase3-providers.example.json",
)
ORCHESTRATOR_SUPPORT = (
    "references/global-rules.md",
    "references/handoff-contracts.md",
    "references/quality-gates.md",
    "references/tool-adapters.md",
    "references/runtime-integration.md",
    "scripts/jobctl.py",
    "scripts/evidence_qc.py",
    "templates/adapter-config.example.json",
    "schemas/job-state.schema.json",
    "schemas/stage-evidence.schema.json",
    "schemas/sentence-shot-map.schema.json",
)
FORBIDDEN_SUFFIXES = (
    ".mp4", ".mov", ".mkv", ".avi", ".mp3", ".wav", ".flac", ".jpg",
    ".jpeg", ".png", ".webp", ".safetensors", ".onnx", ".pt",
    ".bin", ".npz", ".sqlite", ".key", ".pyc", ".pkl",
)


def source_manifest(root: Path = ROOT) -> list[str]:
    """Explicit source-only allowlist: never recursively copy QA datasets."""
    files = [f"skills/{name}/SKILL.md" for name in SKILLS]
    files.extend(
        f"skills/film-review-orchestrator/{name}"
        for name in ORCHESTRATOR_SUPPORT
    )
    for name in RUNTIME_PACKAGES:
        directory = root / name
        if not directory.is_dir():
            raise FileNotFoundError("Missing runtime package: " + name)
        files.extend(p.relative_to(root).as_posix()
                     for p in sorted(directory.glob("*.py")))
    files.extend(SCRIPT_FILES)
    if len(set(files)) != len(files):
        raise ValueError("Duplicate files in runtime manifest")
    for relative in files:
        path = root / relative
        if (path.is_symlink() or not path.is_file()
            or not path.resolve().is_relative_to(root.resolve())):
            raise ValueError("Missing, symlinked or unsafe runtime input: "+relative)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError("Refusing model/data/media input: "+relative)
    return sorted(files)


def diagnose(root: Path = ROOT) -> dict:
    files = source_manifest(root)
    python_ready = sys.version_info >= (3, 10)
    modules = {}
    sys.path.insert(0, str(root))
    try:
        for name in RUNTIME_PACKAGES:
            try:
                importlib.import_module(name)
                modules[name] = "IMPORT_OK"
            except (ImportError, RuntimeError, OSError, ValueError) as exc:
                modules[name] = type(exc).__name__ + ": " + str(exc)[:140]
    finally:
        if sys.path and sys.path[0] == str(root):
            sys.path.pop(0)
    return {
        "package": "Film Review Agent 2.1 source-only",
        "skills_found": len(SKILLS),
        "runtime_files": len(files),
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "python_3_10_plus": python_ready,
        "ffmpeg_found": shutil.which("ffmpeg") is not None,
        "ffprobe_found": shutil.which("ffprobe") is not None,
        "module_imports": modules,
        "source_only_installable": python_ready and all(
            item == "IMPORT_OK" for item in modules.values()
        ),
        "real_model_provider_adapters_bundled": False,
        "real_full_film_n00_n09_ready_without_host_setup": False,
        "requires_operator_provider_configuration": True,
        "requires_real_human_script_voice_pilot_approval": True,
        "contains_test_data_or_movie_assets": False,
    }


def install(project: Path, root: Path = ROOT) -> dict:
    """No overwrite; install agent skills for discovery and a self-contained runtime."""
    project = Path(project).expanduser().resolve(strict=True)
    if not project.is_dir():
        raise ValueError("Project must be a pre-existing authorized directory")
    files = source_manifest(root)
    agent_dir = project / ".agents"
    skills_dir = agent_dir / "skills"
    runtime_dir = agent_dir / "film-review-runtime"
    existing = [str(skills_dir / name) for name in SKILLS
                if (skills_dir / name).exists()]
    if runtime_dir.exists() or runtime_dir.is_symlink() or existing:
        raise FileExistsError("Refusing to overwrite installed runtime/skills: "
                             + ", ".join(([str(runtime_dir)] if runtime_dir.exists() else [])+existing))
    if agent_dir.is_symlink() or skills_dir.is_symlink():
        raise ValueError("Agent directory may not be a symlink")
    # The runtime holds its own copy of skills so Engine21 can load its
    # evidence_qc.py from a path relative to engine21 (no PYTHONPATH hacks).
    runtime_dir.mkdir(parents=True, exist_ok=False)
    try:
        for relative in files:
            source = root / relative
            target = runtime_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target, follow_symlinks=False)
        skills_dir.mkdir(parents=True, exist_ok=True)
        for name in SKILLS:
            src = runtime_dir / "skills" / name
            target = skills_dir / name
            shutil.copytree(src, target, symlinks=False)
    except BaseException:
        # Never delete an old agent install or any preexisting user folder.
        # On a failed fresh install, leave the partial staging tree for inspection.
        raise
    return {
        "status": "INSTALLED_SOURCE_ONLY",
        "skills_installed": len(SKILLS),
        "source_files_in_runtime": len(files),
        "runtime_root": str(runtime_dir),
        "skill_discovery_root": str(skills_dir),
        "example_command": f'cd "{runtime_dir}" && python -m engine21 --help',
        "model_workers_autoconfigured": False,
        "old_data_copied": False,
    }


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description="Source-only Film Review Agent runtime installer")
    sub = cli.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Inspect repo runtime without installing anything")
    ins = sub.add_parser("install", help="Install source-only code into project/.agents")
    ins.add_argument("--project", required=True, type=Path)
    args = cli.parse_args(argv)
    try:
        report = diagnose() if args.command == "doctor" else install(args.project)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if args.command == "install" or report["source_only_installable"] else 2
    except (ValueError, OSError, ImportError, FileNotFoundError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
