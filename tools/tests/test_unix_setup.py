"""Test Unix dependency setup with an isolated PATH and no real installations."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


START = Path(__file__).resolve().parents[1] / 'start.sh'


@unittest.skipIf(os.name == 'nt', 'Unix shell launcher')
class UnixSetupTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='slider setup with spaces ')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bin = self.root / 'fake bin'
        self.bin.mkdir()
        self.events = self.root / 'events.jsonl'
        self.env = dict(os.environ, PATH=str(self.bin), HOME=str(self.root),
                        TMPDIR=str(self.root), SMARTTUBE_SETUP_ROOT=str(self.root),
                        SMARTTUBE_SETUP_PYTHON=sys.executable,
                        SMARTTUBE_SETUP_INSTALL='ok', SMARTTUBE_SETUP_OS='Linux',
                        SMARTTUBE_SETUP_UID='1000')
        self.env.pop('ANDROID_HOME', None)
        self.env.pop('ANDROID_SDK_ROOT', None)
        # Only harmless filesystem helpers may resolve to actual system programs.
        for name in ('mktemp', 'rm', 'dirname', 'basename'):
            real = shutil.which(name)
            self.assertIsNotNone(real, name)
            (self.bin / name).symlink_to(real)
        self.sh = shutil.which('sh')
        self.assertIsNotNone(self.sh)
        self.script = self.root / 'fake-command.py'
        self.script.write_text(r'''import json, os, pathlib, shutil, subprocess, sys
root = pathlib.Path(os.environ['SMARTTUBE_SETUP_ROOT'])
name, args = sys.argv[1], sys.argv[2:]
def record(name, args):
    with (root / 'events.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps([name, args]) + '\n')
def install(name, destination=None):
    directory = destination or root / 'fake bin'
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    target.write_text((root / 'wrapper-template').read_text().replace('TOOL_NAME', name))
    target.chmod(0o700)
if name == 'uname':
    print(os.environ['SMARTTUBE_SETUP_OS'])
elif name == 'id':
    print(os.environ['SMARTTUBE_SETUP_UID'])
elif name == 'sudo':
    record(name, args)
    environment = dict(os.environ, SMARTTUBE_SETUP_ADMIN='1')
    raise SystemExit(subprocess.call(args, env=environment))
elif name in ('python', 'python3'):
    if args and args[0] == '-c':
        raise SystemExit(1 if (root / 'old-python').exists() else 0)
    record('assistant', args[1:])
    if os.environ.get('SMARTTUBE_SETUP_ADMIN'):
        raise SystemExit('The assistant must not run as administrator')
    raise SystemExit(subprocess.call([os.environ['SMARTTUBE_SETUP_PYTHON'], *args]))
elif name == 'adb':
    record(name, args)
    if (root / 'bad-adb').exists():
        raise SystemExit(1)
    print('Android Debug Bridge version 1.0.41')
elif name == 'curl':
    record(name, args)
    target = args[args.index('--output') + 1] if '--output' in args else args[args.index('-o') + 1]
    if 'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh' in args:
        pathlib.Path(target).write_text((root / 'wrapper-template').read_text().replace('TOOL_NAME', 'bootstrap-brew'))
    elif any(value.endswith('/tools/configure_shorts.py') for value in args):
        pathlib.Path(target).write_text('print("assistant fixture launched")\n')
    else:
        raise SystemExit('Unexpected download: no internet access is allowed in this test')
elif name == 'bootstrap-brew':
    record(name, args)
    install('brew')
elif name == 'brew' and args == ['--prefix']:
    record(name, args)
    print(root / 'homebrew prefix')
else:
    record(name, args)
    mode = os.environ['SMARTTUBE_SETUP_INSTALL']
    if mode == 'fail':
        raise SystemExit(41)
    destination = root / 'homebrew prefix' / 'bin' if name == 'brew' else None
    if mode == 'ok' and ('install' in args or '-S' in args or 'add' in args):
        if any(arg in ('python', 'python3') for arg in args):
            install('python3', destination)
            (root / 'old-python').unlink(missing_ok=True)
        if any(arg in ('adb', 'android-tools', 'android-platform-tools') for arg in args):
            install('adb', destination)
            (root / 'bad-adb').unlink(missing_ok=True)
''', encoding='utf-8')
        template = ('#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' ' +
                    shlex.quote(str(self.script)) + ' TOOL_NAME "$@"\n')
        (self.root / 'wrapper-template').write_text(template, encoding='utf-8')
        for name in ('uname', 'id', 'sudo', 'curl'):
            self.executable(name)
        # Route absolute Homebrew discovery into the fixture too. CI hosts may
        # have Homebrew outside PATH; tests must never invoke that installation.
        source = START.read_text(encoding='utf-8')
        for real, fake in (('/opt/homebrew/bin/brew', self.root / 'apple brew' / 'bin' / 'brew'),
                           ('/usr/local/bin/brew', self.root / 'intel brew' / 'bin' / 'brew')):
            self.assertIn(real, source)
            source = source.replace(real, shlex.quote(str(fake)))
        self.launcher = self.root / 'isolated-start.sh'
        self.launcher.write_text(source, encoding='utf-8')

    def executable(self, name):
        target = self.bin / name
        target.write_text((self.root / 'wrapper-template').read_text().replace('TOOL_NAME', name),
                          encoding='utf-8')
        target.chmod(0o700)

    def launch(self, *arguments):
        result = subprocess.run([self.sh, str(self.launcher), *arguments], env=self.env,
                                text=True, input='', capture_output=True, timeout=20)
        events = [json.loads(line) for line in self.events.read_text().splitlines()] if self.events.exists() else []
        self.assertEqual(list(self.root.glob('smarttube-assistant.*')), [],
                         'Downloaded assistant must be cleaned up')
        return result, events

    def assert_launched(self, result, events):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('assistant fixture launched', result.stdout)
        self.assertEqual(sum(name == 'assistant' for name, _ in events), 1)

    def test_installed_tools_do_not_invoke_package_manager(self):
        for name in ('python3', 'adb', 'apt-get'):
            self.executable(name)
        for _ in range(2):
            self.events.unlink(missing_ok=True)
            result, events = self.launch('--profile', 'living room')
            self.assert_launched(result, events)
            self.assertFalse(any(name in ('sudo', 'apt-get') for name, _ in events))
            self.assertIn(['assistant', ['--profile', 'living room']], events)

    def test_usable_tools_later_in_path_prevent_unnecessary_installation(self):
        secondary = self.root / 'working tools with spaces'
        secondary.mkdir()
        template = (self.root / 'wrapper-template').read_text(encoding='utf-8')
        for name in ('python3', 'adb'):
            broken = self.bin / name
            broken.write_text('#!/bin/sh\nexit 1\n', encoding='utf-8')
            broken.chmod(0o700)
            working = secondary / name
            working.write_text(template.replace('TOOL_NAME', name), encoding='utf-8')
            working.chmod(0o700)
        self.executable('apt-get')
        self.env['PATH'] += os.pathsep + str(secondary)
        result, events = self.launch()
        self.assert_launched(result, events)
        self.assertFalse(any(name in ('sudo', 'apt-get') for name, _ in events))
        self.assertTrue(any(name == 'adb' for name, _ in events))

    def test_linux_package_managers_install_missing_dependencies(self):
        for manager, python_package, adb_package in (
                ('apt-get', 'python3', 'adb'), ('dnf', 'python3', 'android-tools'),
                ('pacman', 'python', 'android-tools'), ('zypper', 'python3', 'android-tools'),
                ('apk', 'python3', 'android-tools')):
            with self.subTest(manager=manager):
                for name in ('apt-get', 'dnf', 'pacman', 'zypper', 'apk', 'python3', 'adb'):
                    (self.bin / name).unlink(missing_ok=True)
                self.events.unlink(missing_ok=True)
                self.executable(manager)
                result, events = self.launch()
                self.assert_launched(result, events)
                packages = [argument for name, args in events if name == manager for argument in args]
                self.assertIn(python_package, packages)
                self.assertIn(adb_package, packages)
                self.assertTrue(any(name == 'sudo' for name, _ in events))

    def test_only_missing_python_is_installed(self):
        self.executable('adb')
        self.executable('apt-get')
        result, events = self.launch()
        self.assert_launched(result, events)
        packages = [argument for name, args in events if name == 'apt-get' for argument in args]
        self.assertIn('python3', packages)
        self.assertNotIn('adb', packages)

    def test_only_missing_adb_is_installed(self):
        self.executable('python3')
        self.executable('apt-get')
        result, events = self.launch()
        self.assert_launched(result, events)
        packages = [argument for name, args in events if name == 'apt-get' for argument in args]
        self.assertIn('adb', packages)
        self.assertNotIn('python3', packages)

    def test_unusable_tool_versions_are_rechecked_after_installation(self):
        for name in ('python3', 'adb', 'apt-get'):
            self.executable(name)
        (self.root / 'old-python').touch()
        (self.root / 'bad-adb').touch()
        result, events = self.launch()
        self.assert_launched(result, events)
        self.assertFalse((self.root / 'old-python').exists())
        self.assertFalse((self.root / 'bad-adb').exists())
        self.assertGreaterEqual(sum(name == 'adb' for name, _ in events), 2)

    def test_failed_or_ineffective_installation_stops_before_download(self):
        self.executable('apt-get')
        for mode in ('fail', 'ineffective'):
            with self.subTest(mode=mode):
                self.events.unlink(missing_ok=True)
                self.env['SMARTTUBE_SETUP_INSTALL'] = mode
                result, events = self.launch()
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(name in ('assistant', 'curl') for name, _ in events))

    def test_help_and_offline_backup_do_not_require_adb(self):
        self.executable('python3')
        self.executable('apt-get')
        for arguments in (('--help',), ('-h',), ('--backup', 'my backup.zip'),
                          ('--backup=my backup.zip',)):
            with self.subTest(arguments=arguments):
                self.events.unlink(missing_ok=True)
                result, events = self.launch(*arguments)
                self.assert_launched(result, events)
                self.assertFalse(any(name in ('adb', 'apt-get', 'sudo') for name, _ in events))

    def test_macos_homebrew_handles_paths_with_spaces(self):
        self.env['SMARTTUBE_SETUP_OS'] = 'Darwin'
        self.executable('brew')
        result, events = self.launch()
        self.assert_launched(result, events)
        commands = [args for name, args in events if name == 'brew']
        self.assertTrue(any('install' in args and 'python' in args for args in commands))
        self.assertTrue(any('--cask' in args and 'android-platform-tools' in args for args in commands))
        self.assertFalse(any(name == 'sudo' for name, _ in events))

    def test_macos_bootstraps_missing_homebrew_from_official_installer(self):
        self.env['SMARTTUBE_SETUP_OS'] = 'Darwin'
        result, events = self.launch()
        self.assert_launched(result, events)
        downloads = [args for name, args in events if name == 'curl']
        self.assertEqual(len(downloads), 2)
        self.assertIn('https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh', downloads[0])
        self.assertEqual(sum(name == 'bootstrap-brew' for name, _ in events), 1)
        self.assertTrue((self.root / 'homebrew prefix' / 'bin' / 'python3').exists())
        self.assertTrue((self.root / 'homebrew prefix' / 'bin' / 'adb').exists())

    def test_linux_uses_first_available_supported_package_manager(self):
        for manager in ('apt-get', 'dnf', 'pacman', 'zypper', 'apk'):
            self.executable(manager)
        result, events = self.launch()
        self.assert_launched(result, events)
        self.assertTrue(any(name == 'apt-get' for name, _ in events))
        self.assertFalse(any(name in ('dnf', 'pacman', 'zypper', 'apk') for name, _ in events))

    def test_missing_tools_without_a_supported_manager_stop_safely(self):
        result, events = self.launch()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(name in ('assistant', 'curl', 'sudo') for name, _ in events))

    def test_linux_root_installs_without_sudo(self):
        self.env['SMARTTUBE_SETUP_UID'] = '0'
        self.executable('apt-get')
        result, events = self.launch()
        self.assert_launched(result, events)
        self.assertFalse(any(name == 'sudo' for name, _ in events))


if __name__ == '__main__':
    unittest.main()
