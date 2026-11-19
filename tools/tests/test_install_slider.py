"""Installer tests use synthetic releases and fake ADB; never touch a real TV."""
import copy
import hashlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('install_slider', Path(__file__).resolve().parents[1] / 'install_slider.py')
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)
PAYLOAD = b'synthetic signed APK bytes for installer tests'
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


def fixture(channel='stable'):
    tag = 'v32.68-' + channel + '-slider'
    info = dict(channel=channel, tag=tag, version_name='32.68-slider.4', version_code=245804,
                certificate_sha256=installer.CERTIFICATE, apks=[])
    assets = []
    for name in ['build-info.json', 'SHA256SUMS'] + [
            f'SmartTube_Shorts_Slider_{channel}_32.68-slider_{arch}.apk' for arch in (*installer.ARCHES, 'universal')]:
        assets.append(dict(name=name, size=len(PAYLOAD), browser_download_url=
                           'https://github.com/' + installer.REPOSITORY + '/releases/download/' + tag + '/' + name))
    for arch, asset in zip((*installer.ARCHES, 'universal'), assets[2:]):
        info['apks'].append(dict(file=asset['name'], sha256=DIGEST,
                                architectures=sorted(installer.ARCHES) if arch == 'universal' else [arch]))
    release = dict(tag_name=tag, draft=False, prerelease=channel == 'beta', assets=assets)
    sums = ''.join(row['sha256'] + '  ' + row['file'] + '\n' for row in info['apks']).encode()
    return info, release, sums


def installed(code=245803, name='32.68-slider.3'):
    return dict(versionCode=code, versionName=name, userId='12345', firstInstallTime='2026-10-21 12:00:00')


class FakeAdb:
    def __init__(self, before=None):
        self.before = before
        self.serial = 'tv.example:5555'
        self.commands = []
        self.did_install = False
        self.failure = False
        self.after = installed(245804, '32.68-slider.4')

    def select(self, *args):
        pass

    def prop(self, name):
        return 'armeabi-v7a' if name.startswith('ro.product.cpu.') else 'Synthetic Fire TV'

    def installed(self, package):
        assert package == 'org.smarttube.stable'
        return self.after if self.did_install else self.before

    def run(self, *args, **kwargs):
        self.commands.append(args)
        assert args[:2] == ('install', '-r'), 'Uninstall, launching and all other mutations are forbidden'
        self.did_install = True
        if self.failure:
            return subprocess.CompletedProcess(args, 1, stdout='Failure [INSTALL_FAILED_UPDATE_INCOMPATIBLE]', stderr='')
        return subprocess.CompletedProcess(args, 0, stdout='Performing Streamed Install\nSuccess\n', stderr='')


class InstallerFlowTest(unittest.TestCase):
    def invoke(self, adb, args=(), answer='o', payload=PAYLOAD):
        info, release, _ = fixture()
        with patch.object(installer, 'Adb', return_value=adb), \
             patch.object(installer, 'release_info', return_value=(info, {a['name']: a for a in release['assets']})), \
             patch.object(installer, 'open_url', side_effect=lambda url: io.BytesIO(payload)), \
             patch('builtins.input', return_value=answer):
            return installer.main(list(args))

    def test_new_install_is_stable_and_does_not_launch(self):
        adb = FakeAdb()
        self.assertEqual(self.invoke(adb), 0)
        self.assertEqual(len(adb.commands), 1)
        self.assertEqual(adb.commands[0][:2], ('install', '-r'))

    def test_update_preserves_the_data_identity(self):
        adb = FakeAdb(installed())
        self.assertEqual(self.invoke(adb, ['--yes']), 0)
        self.assertTrue(adb.did_install)
        self.assertEqual(adb.before['userId'], adb.after['userId'])

    def test_official_and_unknown_variants_are_left_untouched(self):
        for name in ['32.68', 'custom-debug', '32.59']:
            adb = FakeAdb(installed(2458, name))
            with self.subTest(name=name), self.assertRaisesRegex(installer.InstallError, 'Aucune désinstallation'):
                self.invoke(adb)
            self.assertEqual(adb.commands, [])

    def test_current_version_is_idempotent(self):
        adb = FakeAdb(installed(245804, '32.68-slider.4'))
        self.assertEqual(self.invoke(adb), 0)
        self.assertEqual(adb.commands, [])

    def test_downgrade_and_inconsistent_same_code_are_refused(self):
        for before in [installed(245805, '32.68-slider.5'), installed(245804, '32.67-slider.4')]:
            adb = FakeAdb(before)
            with self.subTest(before=before), self.assertRaises(installer.InstallError):
                self.invoke(adb)
            self.assertEqual(adb.commands, [])

    def test_dry_run_never_downloads_or_installs(self):
        adb = FakeAdb(installed())
        with patch.object(installer, 'download_apk', side_effect=AssertionError('No download in simulation')):
            self.assertEqual(self.invoke(adb, ['--dry-run']), 0)
        self.assertEqual(adb.commands, [])

    def test_declining_keeps_the_tv_untouched(self):
        adb = FakeAdb()
        self.assertEqual(self.invoke(adb, answer='n'), 0)
        self.assertEqual(adb.commands, [])

    def test_corrupt_download_never_reaches_adb_install(self):
        adb = FakeAdb()
        with self.assertRaises(installer.InstallError):
            self.invoke(adb, payload=b'corrupt')
        self.assertEqual(adb.commands, [])

    def test_android_signature_rejection_does_not_trigger_uninstall_or_retry(self):
        adb = FakeAdb(installed())
        adb.failure = True
        with self.assertRaisesRegex(installer.InstallError, 'Installation refusée'):
            self.invoke(adb)
        self.assertEqual(len(adb.commands), 1)

    def test_unconfirmed_version_or_changed_uid_is_reported(self):
        for after in [None, installed(245803), dict(installed(245804, '32.68-slider.4'), userId='other')]:
            adb = FakeAdb(installed())
            adb.after = after
            with self.subTest(after=after), self.assertRaises(installer.InstallError):
                self.invoke(adb)
            self.assertEqual(len(adb.commands), 1)

    def test_download_only_does_not_initialize_adb(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'download with spaces.apk'
            self.assertEqual(self.invoke(None, ['--download-only', '--arch', 'armeabi-v7a', '--output', str(path)]), 0)
            self.assertEqual(path.read_bytes(), PAYLOAD)


class ReleaseValidationTest(unittest.TestCase):
    def validate(self, info, release, sums, channel='stable'):
        def fake_json(url):
            if url.endswith('/build-info.json'):
                return info
            if url.endswith('/releases/latest'):
                return release
            return [dict(release, draft=True), dict(release, prerelease=False), release]
        with patch.object(installer, 'read_json', side_effect=fake_json), patch.object(installer, 'read_bytes', return_value=sums):
            return installer.release_info(channel)

    def test_stable_and_beta_accept_only_their_own_published_assets(self):
        for channel in ('stable', 'beta'):
            info, release, sums = fixture(channel)
            self.assertEqual(self.validate(info, release, sums, channel)[0], info)

    def test_foreign_url_wrong_certificate_wrong_abi_and_hashes_are_rejected(self):
        for defect in ('url', 'certificate', 'arch', 'hash', 'missing', 'duplicate', 'version'):
            info, release, sums = fixture()
            if defect == 'url': release['assets'][2]['browser_download_url'] = 'https://example.invalid/untrusted.apk'
            if defect == 'certificate': info['certificate_sha256'] = '0' * 64
            if defect == 'arch': info['apks'][0]['architectures'] = ['arm64-v8a']
            if defect == 'hash': info['apks'][0]['sha256'] = '0' * 64
            if defect == 'missing': release['assets'].pop()
            if defect == 'duplicate': release['assets'].append(copy.deepcopy(release['assets'][0]))
            if defect == 'version': info['version_name'] = '32.69-slider.4'
            with self.subTest(defect=defect), self.assertRaises(installer.InstallError):
                self.validate(info, release, sums)

    def test_github_api_and_apk_downloads_use_their_respective_media_types(self):
        calls = []
        def reply(request, **kwargs):
            calls.append(request.get_header('Accept'))
            response = io.BytesIO(b'fixture')
            response.geturl = lambda: request.full_url
            return response
        with patch.object(installer.urllib.request, 'urlopen', side_effect=reply):
            with installer.open_url(installer.API + '/releases/latest'): pass
            with installer.open_url('https://github.com/project/releases/download/file.apk'): pass
        self.assertEqual(calls, ['application/vnd.github+json', 'application/octet-stream'])

    def test_existing_download_file_is_never_deleted_or_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'keep.apk'
            path.write_bytes(b'personal file')
            with patch.object(installer, 'open_url', return_value=io.BytesIO(PAYLOAD)), self.assertRaises(FileExistsError):
                installer.download_apk({'browser_download_url': 'fixture', 'size': len(PAYLOAD)}, DIGEST, path)
            self.assertEqual(path.read_bytes(), b'personal file')

    def test_hash_mismatch_removes_only_the_partial_new_download(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'download.apk'
            with patch.object(installer, 'open_url', return_value=io.BytesIO(PAYLOAD)), self.assertRaises(installer.InstallError):
                installer.download_apk({'browser_download_url': 'fixture', 'size': len(PAYLOAD)}, '0' * 64, path)
            self.assertFalse(path.exists())

    def test_cancelled_download_removes_the_new_partial_file(self):
        class InterruptedDownload(io.BytesIO):
            def read(self, size): raise KeyboardInterrupt()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'interrupted.apk'
            with patch.object(installer, 'open_url', return_value=InterruptedDownload()), self.assertRaises(KeyboardInterrupt):
                installer.download_apk({'browser_download_url': 'fixture', 'size': len(PAYLOAD)}, DIGEST, path)
            self.assertFalse(path.exists())

    def test_architecture_uses_android_support_and_unknown_abi_stops(self):
        self.assertEqual(installer.choose_arch('armeabi-v7a,armeabi'), 'armeabi-v7a')
        self.assertEqual(installer.choose_arch('arm64-v8a,armeabi-v7a'), 'arm64-v8a')
        with self.assertRaises(installer.InstallError): installer.choose_arch('x86_64')


class DeviceSelectionTest(unittest.TestCase):
    def adb(self, replies):
        adb = installer.Adb.__new__(installer.Adb)
        adb.serial = None
        adb.run = lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout='connected', stderr='')
        adb.devices = lambda: next(replies)
        return adb

    def test_multiple_devices_need_selection_and_never_choose_first_with_yes(self):
        adb = self.adb(iter([[['phone', 'device'], ['tv', 'device']]]))
        with self.assertRaises(installer.InstallError): adb.select(noninteractive=True)
        adb = self.adb(iter([[['phone', 'device'], ['tv', 'device']]]))
        with patch('builtins.input', return_value='2'): adb.select()
        self.assertEqual(adb.serial, 'tv')

    def test_connect_selects_the_requested_tv_even_when_a_phone_is_connected(self):
        adb = self.adb(iter([[['phone', 'device']], [['phone', 'device'], ['192.168.1.5:5555', 'device']]]))
        adb.select(connect='192.168.1.5', noninteractive=True)
        self.assertEqual(adb.serial, '192.168.1.5:5555')

    def test_authorization_can_be_accepted_then_rechecked(self):
        adb = self.adb(iter([[['tv', 'unauthorized']], [['tv', 'device']]]))
        with patch('builtins.input', return_value=''): adb.select(serial='tv')
        self.assertEqual(adb.serial, 'tv')

    def test_connect_authentication_error_can_be_resolved_on_the_tv(self):
        adb = self.adb(iter([[], [['192.168.1.5:5555', 'unauthorized']], [['192.168.1.5:5555', 'device']]]))
        adb.run = lambda *args, **kwargs: subprocess.CompletedProcess(args, 1, stdout='failed to authenticate', stderr='')
        with patch('builtins.input', return_value=''):
            adb.select(connect='192.168.1.5')
        self.assertEqual(adb.serial, '192.168.1.5:5555')

    def test_unauthorized_offline_and_invalid_connections_stop(self):
        for state in ('unauthorized', 'offline'):
            adb = self.adb(iter([[['tv', state]]]))
            with self.subTest(state=state), self.assertRaises(installer.InstallError):
                adb.select(serial='tv', noninteractive=True)
        adb = self.adb(iter([[]]))
        with self.assertRaises(installer.InstallError): adb.select(connect='host;bad', noninteractive=True)
