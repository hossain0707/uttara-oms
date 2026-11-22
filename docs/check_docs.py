"""Offline repository documentation checks. Run: python docs/check_docs.py"""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
errors = []
paths = [ROOT / n for n in ('README.md', 'CONTRIBUTING.md', 'CHANGELOG.md')]
paths += list((ROOT / 'docs').rglob('*.md'))
for path in paths:
    content = path.read_text()
    if len(re.findall(r'^```', content, re.M)) % 2:
        errors.append(f'{path.relative_to(ROOT)}: unmatched code fence')
    for target in re.findall(r'\]\(([^\s)]+)', content):
        if ':' in target or target.startswith('#'):
            continue
        file = target.split('#')[0]
        if file and not (path.parent / file).exists():
            errors.append(f'{path.relative_to(ROOT)}: missing link {target}')
ET.parse(ROOT / 'docs/visuals/architecture.svg')
result = json.loads((ROOT / 'docs/evidence/load-smoke-2026-11-22.json').read_text())
assert len(result['attempts']) == 3
assert [a['success'] for a in result['attempts']] == [0, 50, 50]
html = (ROOT / 'docs/visuals/architecture-explorer.html').read_text()
assert len(re.findall(r'<button[^>]*data-tour=', html)) == 5
assert len(re.findall(r'<button[^>]*data-node=', html)) == 7
assert not re.search(r'<(?:script|link)[^>]+(?:src|href)=["\']https?://', html)
assert 'prefers-reduced-motion' in html
assert 'data:image/webp;base64,' in html
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Documentation checks passed: {len(paths)} Markdown files, local links, fences, SVG, evidence and explorer structure.')
