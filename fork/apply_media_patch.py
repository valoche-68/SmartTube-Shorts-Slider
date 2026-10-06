#!/usr/bin/env python3
"""Apply the reviewed media patch after git submodule update --init --recursive."""
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[1]
patch = root / 'fork/mediaservice.patch'
base = ['git', '-C', str(root / 'MediaServiceCore'), 'apply']
if subprocess.run(base + ['--reverse', '--check', str(patch)], capture_output=True).returncode == 0:
    print('Media patch already applied.')
else:
    subprocess.run(base + ['--check', str(patch)], check=True)
    subprocess.run(base + [str(patch)], check=True)
