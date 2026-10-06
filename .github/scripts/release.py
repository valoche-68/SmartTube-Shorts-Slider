#!/usr/bin/env python3
"""Build verified releases from exact upstream tags plus reviewed patches. Never merge master."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / 'fork/config.json').read_text())
REPO = CONFIG['repository']
UPSTREAM = CONFIG['upstream']
ARCHES = ['armeabi-v7a', 'arm64-v8a', 'x86', 'universal']


def run(*args, cwd=ROOT, capture=False):
    result = subprocess.run(list(map(str, args)), cwd=cwd, text=True, stdout=subprocess.PIPE if capture else None, check=True)
    return result.stdout.strip() if capture else ''


def gh(*args):
    return run('gh', *args, capture=True)


def api(path):
    return json.loads(gh('api', path))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def patch_digest():
    return hashlib.sha256(b''.join((ROOT / 'fork' / name).read_bytes() for name in ['shorts.patch', 'mediaservice.patch', 'config.json'])).hexdigest()


def latest(channel):
    # Ignore informational releases, moving aliases, drafts and prereleases of the wrong channel.
    for page in range(1, 6):
        releases = api(f'repos/{UPSTREAM}/releases?per_page=100&page={page}')
        for release in releases:
            if release['draft'] or release['prerelease'] != (channel == 'beta'): continue
            pattern = r'\d+(?:\.\d+)+s' if channel == 'stable' else r'\d+(?:\.\d+)+'
            if re.fullmatch(pattern, release['tag_name']): return release['tag_name']
        if len(releases) < 100: break
    raise RuntimeError('No official release found for ' + channel)


def property_value(value):
    return value.replace('\\', '\\\\').replace('\r', '\\r').replace('\n', '\\n').replace(' ', '\\ ').replace('=', '\\=').replace(':', '\\:')


def signing(folder):
    if os.environ.get('SIGNING_KEY'):
        key = folder / 'release-key.jks'
        key.write_bytes(base64.b64decode(''.join(os.environ['SIGNING_KEY'].split()), validate=True))
        key.chmod(0o600)
        values = {'storeFile': str(key), 'storePassword': os.environ['KEY_STORE_PASSWORD'],
                  'keyAlias': os.environ['ALIAS'], 'keyPassword': os.environ['KEY_PASSWORD']}
        text = ''.join(k + '=' + property_value(v) + '\n' for k, v in values.items())
    else:
        text = (ROOT / 'keystore.properties').read_text()
    path = folder / 'keystore.properties'
    path.write_text(text)
    path.chmod(0o600)


def prepare(channel, upstream_tag, folder):
    if folder.exists(): raise RuntimeError('Build directory already exists: ' + str(folder))
    run('git', 'clone', '--quiet', '--shared', '--no-checkout', ROOT, folder)
    run('git', 'fetch', '--quiet', f'https://github.com/{UPSTREAM}.git', 'refs/tags/' + upstream_tag, cwd=folder)
    run('git', 'checkout', '--quiet', '--detach', 'FETCH_HEAD', cwd=folder)
    upstream_commit = run('git', 'rev-parse', 'HEAD', cwd=folder, capture=True)
    gradle = folder / 'smarttubetv/build.gradle'
    original = gradle.read_text()
    match_name = re.search(r'versionName\s+"([^"]+)"', original)
    match_code = re.search(r'versionCode\s+(\d+)', original)
    if not match_name or not match_code: raise RuntimeError('Unknown upstream version declaration')
    version = match_name[1]
    if version != upstream_tag.removesuffix('s'): raise RuntimeError('Upstream tag and source version disagree')
    revision = CONFIG['revision']
    if not 1 <= revision < 100: raise RuntimeError('Fork revision must be between 1 and 99')
    version_code = int(match_code[1]) * 100 + revision
    if version_code <= 2449 or version_code >= 2_100_000_000: raise RuntimeError('Invalid upgrade version code')
    version_name = version + '-slider.' + str(revision)
    target_tag = f'v{version}-{channel}-slider.{revision}'
    run('git', 'submodule', 'update', '--init', '--recursive', cwd=folder)
    # Check application cleanly; a source change needs review, never a forced merge.
    run('git', 'apply', '--check', ROOT / 'fork/shorts.patch', cwd=folder)
    run('git', 'apply', ROOT / 'fork/shorts.patch', cwd=folder)
    run('git', 'apply', '--check', ROOT / 'fork/mediaservice.patch', cwd=folder / 'MediaServiceCore')
    run('git', 'apply', ROOT / 'fork/mediaservice.patch', cwd=folder / 'MediaServiceCore')
    text = re.sub(r'versionName\s+"[^"]+"', f'versionName "{version_name}"', original, count=1)
    text = re.sub(r'versionCode\s+\d+', f'versionCode {version_code}', text, count=1)
    text = text.replace('def project = "SmartTube"', 'def project = "SmartTube_Shorts_Slider"')
    # One universal build really contains all three supported native ABIs.
    text = text.replace("abiFilters 'armeabi-v7a', 'arm64-v8a'", "abiFilters 'armeabi-v7a', 'arm64-v8a', 'x86'")
    text = text.replace("'x86', 'x86'", "'x86'")
    gradle.write_text(text)
    for flavor in ['stable', 'beta']:
        urls = [f'https://raw.githubusercontent.com/{REPO}/main/smarttube_{flavor}.json']
        if flavor == 'stable': urls.insert(0, f'https://github.com/{REPO}/releases/latest/download/smarttube_stable.json')
        path = folder / f'common/src/st{flavor}/res/values/update_urls.xml'
        path.write_text('<resources>\n<string-array name="update_urls">\n' + ''.join('<item>' + url + '</item>\n' for url in urls) + '</string-array>\n</resources>\n')
    provenance = {'channel': channel, 'upstream_tag': upstream_tag, 'upstream_commit': upstream_commit,
                  'version_name': version_name, 'version_code': version_code, 'tag': target_tag,
                  'fork_commit': run('git', 'rev-parse', 'HEAD', capture=True), 'patch_sha256': patch_digest(),
                  'media_commit': run('git', 'rev-parse', 'HEAD', cwd=folder / 'MediaServiceCore', capture=True)}
    # Release events must use this project's reviewed workflows, not upstream automation.
    for name in ['.github', '.githooks', 'tools', 'docs']:
        target = folder / name
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(ROOT / name, target, ignore=shutil.ignore_patterns('__pycache__'))
    for name in ['README.md', 'README.fr.md', 'LICENSE', '.gitignore', '.gitattributes']:
        shutil.copy2(ROOT / name, folder / name)
    (folder / 'fork').mkdir(exist_ok=True)
    for name in ['config.json', 'shorts.patch', 'mediaservice.patch', 'apply_media_patch.py']:
        shutil.copy2(ROOT / 'fork' / name, folder / 'fork' / name)
    (folder / 'fork/build.json').write_text(json.dumps(provenance, indent=2) + '\n')
    run('git', 'config', 'user.name', 'SmartTube Shorts Slider build', cwd=folder)
    run('git', 'config', 'user.email', '69769543+valoche-68@users.noreply.github.com', cwd=folder)
    run('git', 'add', '-A', '--', 'common', 'smarttubetv', '.github', '.githooks', 'tools', 'docs', 'README.md', 'README.fr.md', 'LICENSE', '.gitignore', '.gitattributes', cwd=folder)
    run('git', 'add', '-f', '--', 'fork', cwd=folder)
    run('git', 'commit', '--quiet', '-m', f'Build {target_tag} from {upstream_tag}', cwd=folder)
    provenance['source_commit'] = run('git', 'rev-parse', 'HEAD', cwd=folder, capture=True)
    signing(folder)
    sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if not sdk and (ROOT / 'local.properties').exists(): shutil.copy2(ROOT / 'local.properties', folder / 'local.properties')
    elif sdk: (folder / 'local.properties').write_text('sdk.dir=' + property_value(sdk) + '\n')
    return provenance


def sdk_tool(name):
    sdk = Path(os.environ.get('ANDROID_HOME', os.environ.get('ANDROID_SDK_ROOT', str(Path.home() / 'Android/Sdk'))))
    paths = list((sdk / 'build-tools').glob('*/' + name))
    if not paths: raise RuntimeError('Android build tool missing: ' + name)
    return sorted(paths)[-1]


def verify_apk(apk, provenance, arch):
    badging = run(sdk_tool('aapt'), 'dump', 'badging', apk, capture=True)
    expected = {'name': 'org.smarttube.' + provenance['channel'], 'versionCode': str(provenance['version_code']),
                'versionName': provenance['version_name']}
    package = badging.splitlines()[0]
    for field, value in expected.items():
        if f"{field}='{value}'" not in package: raise RuntimeError(f'APK {field} mismatch: {apk.name}')
    signature = run(sdk_tool('apksigner'), 'verify', '--print-certs', apk, capture=True)
    certificates = re.findall(r'certificate SHA-256 digest: ([a-f0-9]+)', signature)
    if certificates != [CONFIG['certificate_sha256']]: raise RuntimeError('Unexpected APK signing certificate')
    with zipfile.ZipFile(apk) as archive:
        abis = {name.split('/')[1] for name in archive.namelist() if name.startswith('lib/') and name.endswith('.so')}
    if abis != (set(ARCHES[:-1]) if arch == 'universal' else {arch}):
        raise RuntimeError(f'Incorrect native architectures in {apk.name}: {sorted(abis)}')
    resources = run(sdk_tool('aapt'), 'dump', '--values', 'resources', apk, capture=True)
    expected_url = f'https://raw.githubusercontent.com/{REPO}/main/smarttube_{provenance["channel"]}.json'
    if expected_url not in resources: raise RuntimeError('Fork OTA address missing from compiled APK')
    forbidden = ['SmartTubeNext/releases/download/latest/smarttube_', 'yuliskov/SmartTube/releases/download/latest/smarttube_', 'smarttube_beta2.json']
    if any(value in resources for value in forbidden): raise RuntimeError('Official/obsolete OTA address in compiled APK')
    return {'file': apk.name, 'sha256': digest(apk), 'architectures': sorted(abis)}


def make_assets(folder, provenance):
    assets = folder / 'release_assets'
    assets.mkdir(exist_ok=True)
    records = []
    for arch in ARCHES:
        name = f'SmartTube_Shorts_Slider_{provenance["channel"]}_{provenance["version_name"]}_{arch}.apk'
        source = folder / f'smarttubetv/build/outputs/apk/st{provenance["channel"]}/release' / name
        records.append(verify_apk(source, provenance, arch))
        shutil.copy2(source, assets / name)
    provenance['apks'] = records
    provenance['certificate_sha256'] = CONFIG['certificate_sha256']
    (assets / 'build-info.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (assets / 'SHA256SUMS').write_text(''.join(record['sha256'] + '  ' + record['file'] + '\n' for record in records))
    base = f'https://github.com/{REPO}/releases/download/{provenance["tag"]}/'
    downloads = {}
    for record, arch in zip(records, ARCHES):
        key = 'downloadUrlList' if arch == 'armeabi-v7a' else 'downloadUrlList_' + arch
        downloads[key] = [base + record['file']]
    notes_fr = ['Bouton Shorts automatique ON/OFF, masquable dans les réglages.',
                'Navigation native haut/bas et lecture automatique activées sur les nouveaux profils.',
                'Préparation facultative des informations du Short suivant ; gain de vitesse non mesuré.',
                'Tampons et pagination officiels ; aucune réserve garantie de 10 à 20 vidéos.']
    notes_en = ['Hideable Shorts auto-scroll button.', 'Native up/down navigation and auto-play enabled for new profiles.',
                'Optional next-Short playback information preparation; speed benefit not measured.', 'Official buffering and pagination; no guaranteed queue of 10–20 videos.']
    if CONFIG['revision'] >= 2:
        notes_fr[:0] = ['Reconnaissance des Shorts conservée lors des copies et de la reprise de lecture.',
                       'Navigation et enchaînement parmi les Shorts disponibles, y compris sans playlist de section.']
        notes_en[:0] = ['Shorts identity retained through copies and playback restoration.',
                       'Navigation and autoplay select available Shorts even with the section playlist disabled.']
    metadata = {'package': downloads, provenance['version_name']: {'versionCode': provenance['version_code'],
                'changelog': notes_en, 'changelog_fr': notes_fr}}
    payload = json.dumps(metadata, indent=2, ensure_ascii=False) + '\n'
    (assets / f'smarttube_{provenance["channel"]}.json').write_text(payload)
    if provenance['channel'] == 'stable': (assets / 'smarttube_stable2.json').write_text(payload)
    notes = f'''## Français
Base officielle : [{provenance['upstream_tag']}](https://github.com/{UPSTREAM}/tree/{provenance['upstream_commit']}).
Version APK : **{provenance['version_name']}**, code Android **{provenance['version_code']}**.

''' + '\n'.join('- ' + item for item in notes_fr) + '''

Les tests automatisés et les contrôles des APK précèdent la publication. L'essai sur la Fire TV du mainteneur et la mesure de vitesse restent à faire.
Les mises à jour de Shorts Slider conservent la même signature ; ne pas désinstaller l'application pour la mettre à jour. Depuis l'application officielle, consulter le guide de sauvegarde et de migration.

## English
''' + '\n'.join('- ' + item for item in notes_en) + f'''

Built from the exact upstream tag, with its pinned submodules and the reviewed fork patches.
See [source](https://github.com/{REPO}/tree/{provenance['source_commit']}), `build-info.json` and `SHA256SUMS` for provenance.
The maintainer's Fire TV test and speed comparison remain pending.
'''
    (folder / 'release_notes.md').write_text(notes)
    return assets


def build(folder, provenance):
    flavor = 'St' + provenance['channel']
    run('bash', 'gradlew', ':common:test' + flavor + 'DebugUnitTest', '--tests', '*ShortsPreferencesTest', '--tests', '*NextVideoPreloaderTest',
        '--tests', '*PlaybackNonceIsolationTest', '--tests', '*VideoShortsClassificationTest', '--tests', '*ShortsNavigationTest',
        ':youtubeapi:test' + flavor + 'DebugUnitTest', '--tests', '*ShortsIdentityTest',
        ':smarttubetv:assemble' + flavor + 'Release', '--console=plain', cwd=folder)
    return make_assets(folder, provenance)


def commit_metadata(assets, channel):
    names = [f'smarttube_{channel}.json'] + (['smarttube_stable2.json'] if channel == 'stable' else [])
    for name in names: shutil.copy2(assets / name, ROOT / name)
    run('git', 'add', '--', *names)
    if subprocess.run(['git', 'diff', '--cached', '--quiet', '--', *names], cwd=ROOT).returncode:
        run('git', 'commit', '-m', f'Update verified {channel} OTA metadata', '--', *names)
        run('git', 'push', 'origin', 'HEAD:main')


def publish(folder, provenance, assets):
    tag = provenance['tag']
    # Push the exact source commit, not the orchestration checkout.
    remote = f'https://github.com/{REPO}.git'
    run('git', 'push', remote, provenance['source_commit'] + ':refs/tags/' + tag, cwd=folder)
    args = ['release', 'create', tag, '--repo', REPO, '--verify-tag', '--draft', '--title',
            f'SmartTube Shorts Slider {provenance["upstream_tag"].removesuffix("s")} — {provenance["channel"]}',
            '--notes-file', str(folder / 'release_notes.md')]
    if provenance['channel'] == 'beta': args.append('--prerelease')
    gh(*args, *map(str, assets.iterdir()))
    # Verify remote draft downloads before making this version visible.
    with tempfile.TemporaryDirectory() as temp:
        gh('release', 'download', tag, '--repo', REPO, '--dir', temp)
        for path in assets.iterdir():
            if digest(Path(temp) / path.name) != digest(path): raise RuntimeError('Uploaded release asset mismatch')
    gh('release', 'edit', tag, '--repo', REPO, '--draft=false', '--latest=' + ('true' if provenance['channel'] == 'stable' else 'false'))
    commit_metadata(assets, provenance['channel'])
    gh('workflow', 'run', 'virustotal_scan.yml', '--repo', REPO, '-f', 'release_tag=' + tag)


def state_read():
    result = subprocess.run(['gh', 'api', f'repos/{REPO}/contents/release-state.json?ref=automation-state'], capture_output=True, text=True)
    if result.returncode:
        if '404' in result.stderr: return {}, None
        raise RuntimeError('Cannot read automation state')
    data = json.loads(result.stdout)
    return json.loads(base64.b64decode(data['content'])), data['sha']


def state_write(state, sha):
    if sha is None:
        result = subprocess.run(['gh', 'api', f'repos/{REPO}/git/ref/heads/automation-state'], capture_output=True)
        if result.returncode:
            head = api(f'repos/{REPO}/git/ref/heads/main')['object']['sha']
            gh('api', f'repos/{REPO}/git/refs', '-f', 'ref=refs/heads/automation-state', '-f', 'sha=' + head)
    data = {'message': 'Record release automation result', 'branch': 'automation-state',
            'content': base64.b64encode(json.dumps(state, indent=2).encode()).decode()}
    if sha: data['sha'] = sha
    with tempfile.NamedTemporaryFile('w', suffix='.json') as f:
        json.dump(data, f); f.flush()
        gh('api', '--method', 'PUT', f'repos/{REPO}/contents/release-state.json', '--input', f.name)


def existing_release(tag):
    result = subprocess.run(['gh', 'release', 'view', tag, '--repo', REPO, '--json', 'isDraft'], capture_output=True, text=True)
    if result.returncode:
        if 'release not found' in result.stderr.lower() or '404' in result.stderr: return None
        raise RuntimeError('Cannot inspect release')
    return json.loads(result.stdout)


def automate(channels, retry=False):
    state, sha = state_read()
    failed = False
    for channel in channels:
        tag = latest(channel)
        source = gh('api', f'repos/{UPSTREAM}/commits/{tag}', '--jq', '.sha')
        key = f'{channel}:{source}:{patch_digest()}'
        if not retry and state.get(key, {}).get('status') in ['failed', 'published']:
            print(f'{channel}: source already processed; manual retry available.')
            continue
        folder = ROOT / 'release-build' / channel
        if folder.exists(): shutil.rmtree(folder)
        try:
            target = f'v{tag.removesuffix("s")}-{channel}-slider.{CONFIG["revision"]}'
            existing = existing_release(target)
            if existing:
                # Never silently replace an already published binary.
                if existing['isDraft']: raise RuntimeError('A draft exists; inspect and remove both the draft and its custom tag before retrying')
                with tempfile.TemporaryDirectory() as temp:
                    gh('release', 'download', target, '--repo', REPO, '--dir', temp, '--pattern', '*.json')
                    info = json.loads((Path(temp) / 'build-info.json').read_text())
                    if info['patch_sha256'] != patch_digest() or info['upstream_commit'] != source:
                        raise RuntimeError('Published tag has different sources; increment fork revision')
                    commit_metadata(Path(temp), channel)
            else:
                info = prepare(channel, tag, folder)
                assets = build(folder, info)
                publish(folder, info, assets)
            status = 'published'
        except (subprocess.CalledProcessError, RuntimeError, OSError, KeyError, ValueError) as error:
            print(f'{channel} failed: {error}', file=sys.stderr)
            status = 'failed'
            failed = True
        finally:
            for name in ['keystore.properties', 'release-key.jks']:
                (folder / name).unlink(missing_ok=True)
        state[key] = {'status': status, 'tag': tag, 'run_id': os.environ.get('GITHUB_RUN_ID', 'local')}
        state_write(state, sha)
        state, sha = state_read()
    if failed: raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'build', 'automate'])
    parser.add_argument('--channel', choices=['stable', 'beta', 'all'], default='all')
    parser.add_argument('--tag')
    parser.add_argument('--folder', type=Path)
    parser.add_argument('--retry', action='store_true')
    args = parser.parse_args()
    if args.command == 'automate': automate(['stable', 'beta'] if args.channel == 'all' else [args.channel], args.retry)
    else:
        if args.channel == 'all' or args.folder is None: parser.error('A single channel and --folder are required')
        folder = args.folder.resolve()
        if args.command == 'prepare':
            info = prepare(args.channel, args.tag or latest(args.channel), folder)
            (folder / 'release-plan.json').write_text(json.dumps(info, indent=2))
        else:
            info = json.loads((folder / 'release-plan.json').read_text())
            build(folder, info)
