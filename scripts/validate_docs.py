"""Dependency-free structural checks, not runtime validation."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r'(?<!!)\[[^\]]*\]\(([^)]+)\)')
JSON_RE = re.compile(r'(?m)^(```|~~~)json\s*\n(.*?)^\1\s*$', re.S | re.M)
REQUIRED = ('schema_version', 'job_id', 'source_sha256', 'generator', 'produced_at')

def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors = []
    entry = root / 'SKILL.md'
    if not entry.is_file():
        errors.append('Missing SKILL.md')
    elif not re.match(r'\A---\s*\n.*?^name:\s*\S+.*?^description:\s*Use when', entry.read_text(encoding='utf-8'), re.S | re.M):
        errors.append('SKILL.md missing valid frontmatter name/Use when description')
    for path in root.rglob('*.md'):
        if '.git' in path.parts:
            continue
        content = path.read_text(encoding='utf-8')
        for raw in LINK_RE.findall(content):
            ref = raw.strip().split(' ', 1)[0].strip('<>')
            if not ref or ref.startswith(('#', 'https:', 'http:', 'mailto:', 'data:')):
                continue
            ref = unquote(ref.split('#', 1)[0].split('?', 1)[0])
            target = (path.parent / ref).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(f'{path.relative_to(root)}: Outside repository: {raw}')
                continue
            if not target.exists():
                errors.append(f'{path.relative_to(root)}: Missing target: {raw}')
        for marker, block in JSON_RE.findall(content):
            try:
                obj = json.loads(block)
            except json.JSONDecodeError as err:
                errors.append(f'{path.relative_to(root)}: Invalid JSON: {err}')
                continue
            if isinstance(obj, dict) and 'schema_version' in obj:
                missing = [key for key in REQUIRED if key not in obj]
                if missing:
                    errors.append(f'{path.relative_to(root)}: Missing envelope: {missing}')
                if 'source_sha256' in obj and not re.fullmatch(r'[0-9a-fA-F]{64}', str(obj['source_sha256'])):
                    errors.append(f'{path.relative_to(root)}: Invalid source_sha256')
    return sorted(errors)

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for item in errors:
            print('ERROR:', item)
        print(f'DOC VALIDATION FAIL: {len(errors)} issue(s)')
        return 1
    print('DOC VALIDATION PASS (structure only, not runtime or agent behavior)')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
