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
