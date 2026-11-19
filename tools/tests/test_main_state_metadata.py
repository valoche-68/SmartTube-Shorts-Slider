"""Check OTA publication after state commits advance the same main branch."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[2] / '.github/scripts/release.py'
SPEC = importlib.util.spec_from_file_location('release_main_state', PATH)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class MainStateMetadataTest(unittest.TestCase):
    def git(self, folder, *args):
        return subprocess.run(['git', '-C', str(folder), *args], check=True, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.seed = root / 'seed'
        self.seed.mkdir()
        self.git(self.seed, 'init', '--initial-branch=main')
        self.configure(self.seed)
        (self.seed / '.github').mkdir()
        (self.seed / '.github/release-state.json').write_text('{}\n')
        (self.seed / 'smarttube_beta.json').write_text('old metadata\n')
        self.git(self.seed, 'add', '.')
        self.git(self.seed, 'commit', '-m', 'Initial synthetic files')
        self.remote = root / 'remote.git'
        self.git(self.seed, 'clone', '--bare', str(self.seed), str(self.remote))
        self.publisher = root / 'publisher'
        self.writer = root / 'state-writer'
        for folder in (self.publisher, self.writer):
            self.git(root, 'clone', str(self.remote), str(folder))
            self.configure(folder)
        self.state = {'stable:source:patch': {'status': 'published'}}
        (self.writer / '.github/release-state.json').write_text(json.dumps(self.state))
        self.git(self.writer, 'add', '.github/release-state.json')
        self.git(self.writer, 'commit', '-m', 'State written by previous channel')
        self.git(self.writer, 'push', 'origin', 'main')
        self.assets = root / 'assets'
        self.assets.mkdir()
        (self.assets / 'smarttube_beta.json').write_text('verified new metadata\n')

    def configure(self, folder):
        self.git(folder, 'config', 'user.name', 'Synthetic release test')
        self.git(folder, 'config', 'user.email', 'test@example.invalid')
        self.git(folder, 'config', 'commit.gpgsign', 'false')

    def publish_metadata(self):
        original_run = release.run

        def run_in_fixture(*args, **kwargs):
            kwargs.setdefault('cwd', self.publisher)
            return original_run(*args, **kwargs)

        with patch.object(release, 'ROOT', self.publisher), patch.object(release, 'run', side_effect=run_in_fixture):
            release.commit_metadata(self.assets, 'beta')

    def test_next_channel_preserves_remote_state_and_pushes_metadata_without_force(self):
        self.publish_metadata()
        state = json.loads(self.git(self.remote, 'show', 'main:.github/release-state.json'))
        self.assertEqual(state, self.state)
        self.assertEqual(self.git(self.remote, 'show', 'main:smarttube_beta.json'), 'verified new metadata')
        self.assertEqual(json.loads((self.publisher / '.github/release-state.json').read_text()), self.state)

    def test_divergent_history_stops_before_replacing_ota_files(self):
        (self.publisher / 'local-only.txt').write_text('preserve')
        self.git(self.publisher, 'add', 'local-only.txt')
        self.git(self.publisher, 'commit', '-m', 'Unpublished local history')
        with self.assertRaises(subprocess.CalledProcessError):
            self.publish_metadata()
        self.assertEqual((self.publisher / 'smarttube_beta.json').read_text(), 'old metadata\n')
        self.assertEqual(self.git(self.remote, 'show', 'main:smarttube_beta.json'), 'old metadata')
