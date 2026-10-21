import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location('configure_shorts', Path(__file__).parents[1] / 'configure_shorts.py')
cfg = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cfg)
PKG = 'org.smarttube.stable'
ROOT = 'data/' + PKG + '/Backup/'


def fixture(legacy=False, profile='', package=PKG, version_code=None):
    root = 'data/' + package + '/Backup/'
    values = {cfg.TWEAKS: ['null'] * 61, cfg.PLAYER: ['null'] * 63, cfg.GENERAL: ['null'] * 73}
    values[cfg.TWEAKS][44] = 'true'
    values[cfg.TWEAKS][45] = 'true'
    values[cfg.TWEAKS][57] = 'false'
    if version_code is not None: values[cfg.GENERAL][39] = str(version_code)
    prefix = profile + '_' if profile else ''
    entries = {root + 'shared_prefs/yt_service_prefs.xml': b'<map><string name="account">synthetic</string></map>'}
    xml = '<map><boolean name="multi_profiles" value="' + ('true' if profile else 'false') + '"/>'
    xml += '<string name="last_profile_name">' + profile + '</string>'
    for key, array in values.items():
        text = cfg.DELIM.join(array)
        if legacy: xml += '<string name="' + prefix + key + '">' + text + '</string>'
        else: entries[root + 'files/app_prefs/' + prefix + key] = text.encode()
    xml += '<string name="unrelated">unchanged</string></map>'
    entries[root + 'shared_prefs/' + package + '_preferences.xml'] = xml.encode()
    return archive(entries)


def archive(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for key, value in entries.items(): z.writestr(key, value)
    return out.getvalue()


class ConfigureTest(unittest.TestCase):
    def test_files_and_legacy_profiles_preserve_unrelated_data(self):
        for legacy in (True, False):
            for profile in ('', 'test_profile'):
                original = cfg.Backup(fixture(legacy, profile), PKG)
                backup = cfg.Backup(fixture(legacy, profile), PKG)
                changes = cfg.configure(backup, 'up-down', True, True)
                after = cfg.Backup(backup.encode(), PKG)
                self.assertEqual(after.effective('vertical'), 'true')
                self.assertEqual(after.effective('horizontal'), 'false')
                self.assertEqual(after.effective('loop'), 'false')
                self.assertEqual(after.effective('playback'), '2')
                self.assertEqual(after.entries[ROOT + 'shared_prefs/yt_service_prefs.xml'], original.entries[ROOT + 'shared_prefs/yt_service_prefs.xml'])
                self.assertEqual(after.xml_values['unrelated'].text, 'unchanged')
                self.assertEqual(cfg.configure(after, 'up-down', True, True), {})
                # Changes made later to an unrelated slot survive selective undo.
                after.set_slot(cfg.PLAYER, 10, '987')
                cfg.undo(after, {'schema': 1, 'package': PKG, 'profile': profile, 'changes': changes})
                self.assertEqual(after.state(), original.state())
                self.assertEqual(after.get_slot(cfg.PLAYER, 10), '987')

    def test_undo_does_not_overwrite_new_user_choice(self):
        backup = cfg.Backup(fixture(), PKG)
        changes = cfg.configure(backup, 'up-down')
        cfg.configure(backup, 'left-right')
        with self.assertRaises(cfg.ConfigError):
            cfg.undo(backup, {'schema': 1, 'package': PKG, 'profile': '', 'changes': changes})

    def test_archive_and_old_fork_rejections(self):
        for entries in ({'../escape': b'x'}, {'/absolute': b'x'}, {'nothing': b'x'}):
            with self.assertRaises(cfg.ConfigError): cfg.Backup(archive(entries), PKG)
        backup = cfg.Backup(fixture(), PKG)
        backup.set_slot(cfg.TWEAKS, 61, 'true')
        with self.assertRaises(cfg.ConfigError): cfg.Backup(backup.encode(), PKG)
        with self.assertRaises(cfg.ConfigError): cfg.Backup(fixture(), 'org.smarttube.beta')

    def test_dry_run_writes_nothing_and_unknown_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'backup.zip'
            path.write_bytes(fixture())
            args = ['--backup', str(path), '--version', '32.56', '--navigation', 'up-down', '--dry-run', '--output', str(Path(folder) / 'result')]
            self.assertEqual(cfg.main(args), 0)
            self.assertFalse((Path(folder) / 'result').exists())
            with patch('builtins.input', return_value='consulter'):
                self.assertEqual(cfg.main(['--backup', str(path), '--version', '32.56']), 0)
            # Reproduce Windows output redirected by CI, including ASCII-only terminals.
            for encoding in ('cp1252', 'ascii'):
                with io.TextIOWrapper(io.BytesIO(), encoding=encoding) as stream:
                    with patch.object(cfg.sys, 'stdout', stream):
                        self.assertEqual(cfg.main(args), 0)
            args[3] = '99.99'
            with self.assertRaises(cfg.ConfigError): cfg.main(args)

    def test_horizontal_resets_conflicting_volume_and_off_keeps_other_remaps(self):
        backup = cfg.Backup(fixture(), PKG)
        backup.set_slot(cfg.GENERAL, 54, 'true')
        cfg.configure(backup, 'left-right', False)
        self.assertEqual(backup.effective('left_volume'), 'false')
        self.assertEqual(backup.effective('loop'), 'true')
        cfg.configure(backup, 'off')
        self.assertEqual(backup.effective('vertical'), 'false')
        self.assertEqual(backup.effective('horizontal'), 'false')

    def test_3268_backup_is_supported_for_both_channels_without_modifying_the_original(self):
        for channel in ('stable', 'beta'):
            for legacy in (False, True):
                with self.subTest(channel=channel, legacy=legacy), tempfile.TemporaryDirectory() as folder:
                    package = 'org.smarttube.' + channel
                    original = fixture(legacy=legacy, package=package, version_code=2458)
                    source = Path(folder) / 'backup.zip'
                    source.write_bytes(original)
                    target = Path(folder) / 'result'
                    self.assertEqual(cfg.main(['--backup', str(source), '--version', '32.68',
                                              '--channel', channel, '--navigation', 'up-down',
                                              '--autoplay', 'on', '--section', 'on', '--output', str(target)]), 0)
                    self.assertEqual(source.read_bytes(), original)
                    self.assertEqual((target / 'original.zip').read_bytes(), original)
                    backup = cfg.Backup((target / 'configured.zip').read_bytes(), package)
                    self.assertEqual(backup.get_slot(cfg.GENERAL, 39), '2458')
                    self.assertEqual(backup.effective('vertical'), 'true')
                    self.assertEqual(backup.effective('horizontal'), 'false')
                    self.assertEqual(backup.effective('loop'), 'false')
                    self.assertEqual(backup.effective('playback'), '2')
                    self.assertEqual(backup.effective('section'), 'true')

    def test_3268_version_validation_rejects_different_codes_and_custom_builds(self):
        adb = cfg.Adb.__new__(cfg.Adb)
        for name, code, valid in (('32.68', 2458, True), ('32.68', 2457, False),
                                   ('32.68-slider.4', 245804, False), ('32.69', 2459, False)):
            with self.subTest(name=name, code=code):
                reply = type('Reply', (), {'stdout': 'versionName=' + name + '\nversionCode=' + str(code)})()
                with patch.object(adb, 'shell', return_value=reply):
                    if valid:
                        self.assertEqual(adb.version(PKG), '32.68')
                    else:
                        with self.assertRaises(cfg.ConfigError): adb.version(PKG)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'backup.zip'
            source.write_bytes(fixture(version_code=2446))
            target = Path(folder) / 'result'
            with self.assertRaises(cfg.ConfigError):
                cfg.main(['--backup', str(source), '--version', '32.68', '--navigation', 'up-down',
                          '--output', str(target)])
            self.assertFalse(target.exists())
