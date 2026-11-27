#!/usr/bin/env python3
"""Apply the reviewed patch for the official media submodule pinned by this checkout."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def patch_for_head(config, head):
    bases = {config['media_base_commit']: 'mediaservice.patch'}
    beta_base = config.get('media_beta_base_commit')
    if beta_base and beta_base != config['media_base_commit']:
        bases[beta_base] = 'mediaservice-beta.patch'
    if head not in bases:
        raise RuntimeError('Unknown media submodule commit; review its sources and patch before building: ' + head)
    return bases[head]


def main():
    config = json.loads((ROOT / 'fork/config.json').read_text())
    media = ROOT / 'MediaServiceCore'
    head = subprocess.check_output(['git', '-C', str(media), 'rev-parse', 'HEAD'], text=True).strip()
    patch = ROOT / 'fork' / patch_for_head(config, head)
    base = ['git', '-C', str(media), 'apply']
    if subprocess.run(base + ['--reverse', '--check', str(patch)], capture_output=True).returncode == 0:
        print('Media patch already applied: ' + patch.name)
    else:
        subprocess.run(base + ['--check', str(patch)], check=True)
        subprocess.run(base + [str(patch)], check=True)


if __name__ == '__main__':
    main()
