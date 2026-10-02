import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

repo = os.environ['GH_REPO']
tag = os.environ['TAG']
start, end = '<!-- virustotal:start -->', '<!-- virustotal:end -->'
notes = subprocess.check_output(['gh', 'release', 'view', tag, '--repo', repo, '--json', 'body', '-q', '.body'], text=True)
if start in notes:
    if end not in notes: raise SystemExit('Incomplete report markers; leaving release notes unchanged.')
    before, tail = notes.split(start, 1)
    notes = before.rstrip() + tail.split(end, 1)[1]
report = [start, '## VirusTotal', 'Consulter les rapports ci-dessous pour leur état réel. Aucun verdict antivirus n’est affirmé par ce script.', '']
for file in sorted(Path('release_assets').glob('*.apk')):
    sha = hashlib.sha256(file.read_bytes()).hexdigest()
    report.append(f'- [{file.name} — rapport](https://www.virustotal.com/gui/file/{sha}/detection)')
report.append(end)
with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.md') as f:
    f.write(notes.rstrip() + '\n\n' + '\n'.join(report) + '\n'); f.flush()
    subprocess.run(['gh', 'release', 'edit', tag, '--repo', repo, '--notes-file', f.name], check=True)
