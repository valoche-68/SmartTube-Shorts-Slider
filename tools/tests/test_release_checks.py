import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

PATH = Path(__file__).resolve().parents[2] / '.github/scripts/release.py'
SPEC = importlib.util.spec_from_file_location('release_checks', PATH)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseChecksTest(unittest.TestCase):
    def test_public_names_hide_revision_without_changing_apk_or_update_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            output = folder / 'smarttubetv/build/outputs/apk/ststable/release'
            output.mkdir(parents=True)
            info = dict(channel='stable', upstream_tag='32.56s', upstream_commit='official',
                        source_commit='exact-source', version_name='32.56-slider.2', version_code=244602,
                        tag=release.public_tag('32.56s', 'stable'))
            originals = {}
            for arch in release.ARCHES:
                name = 'SmartTube_Shorts_Slider_stable_32.56-slider.2_' + arch + '.apk'
                originals[arch] = ('original signed bytes ' + arch).encode()
                (output / name).write_bytes(originals[arch])
            def checked(path, provenance, arch):
                self.assertEqual(provenance['version_name'], '32.56-slider.2')
                return dict(file=path.name, sha256=release.digest(path), architectures=[arch])
            with patch.object(release, 'verify_apk', side_effect=checked):
                assets = release.make_assets(folder, info)
            self.assertEqual(info['tag'], 'v32.56-stable-slider')
            for record, arch in zip(info['apks'], release.ARCHES):
                self.assertNotIn('slider.2', record['file'])
                self.assertEqual((assets / record['file']).read_bytes(), originals[arch])
            metadata = json.loads((assets / 'smarttube_stable.json').read_text())
            self.assertEqual(metadata['32.56-slider.2']['versionCode'], 244602)
            self.assertNotIn('slider.2', json.dumps(metadata['package']))
            self.assertNotIn('slider.2', (folder / 'release_notes.md').read_text())

    def test_release_selection_ignores_aliases_announcements_and_wrong_channel(self):
        candidates = [dict(draft=False, prerelease=False, tag_name='notification2'),
                      dict(draft=False, prerelease=True, tag_name='99.00'),
                      dict(draft=True, prerelease=False, tag_name='33.00s'),
                      dict(draft=False, prerelease=False, tag_name='32.56s')]
        with patch.object(release, 'api', return_value=candidates):
            self.assertEqual(release.latest('stable'), '32.56s')
            self.assertEqual(release.latest('beta'), '99.00')

    def test_properties_preserve_special_characters_without_shell_interpolation(self):
        self.assertEqual(release.property_value(' space=one\\two\n'), '\\ space\\=one\\\\two\\n')

    def test_binary_checks_reject_wrong_signature_architecture_and_ota(self):
        info = dict(channel='stable', version_code=244601, version_name='32.56-slider.1')
        badging = "package: name='org.smarttube.stable' versionCode='244601' versionName='32.56-slider.1'"
        cert = 'Signer #1 certificate SHA-256 digest: ' + release.CONFIG['certificate_sha256']
        resource = 'https://raw.githubusercontent.com/' + release.REPO + '/main/smarttube_stable.json'
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / 'fixture.apk'
            with zipfile.ZipFile(apk, 'w') as z: z.writestr('lib/armeabi-v7a/test.so', b'synthetic')
            with patch.object(release, 'sdk_tool', side_effect=lambda name: name):
                with patch.object(release, 'run', side_effect=[badging, cert, resource]):
                    self.assertEqual(release.verify_apk(apk, info, 'armeabi-v7a')['architectures'], ['armeabi-v7a'])
                with patch.object(release, 'run', side_effect=[badging, cert.replace(release.CONFIG['certificate_sha256'], '0' * 64)]):
                    with self.assertRaises(RuntimeError): release.verify_apk(apk, info, 'armeabi-v7a')
                with patch.object(release, 'run', side_effect=[badging, cert]):
                    with self.assertRaises(RuntimeError): release.verify_apk(apk, info, 'universal')
                with patch.object(release, 'run', side_effect=[badging, cert, 'https://official.invalid/update']):
                    with self.assertRaises(RuntimeError): release.verify_apk(apk, info, 'armeabi-v7a')

    def test_failed_revision_is_skipped_until_manual_retry(self):
        key = 'stable:source:patch'
        with patch.object(release, 'state_read', return_value=({key: {'status': 'failed'}}, 'state-sha')), \
             patch.object(release, 'latest', return_value='32.56s'), \
             patch.object(release, 'gh', return_value='source'), \
             patch.object(release, 'patch_digest', return_value='patch'), \
             patch.object(release, 'prepare') as prepare:
            release.automate(['stable'])
            prepare.assert_not_called()
