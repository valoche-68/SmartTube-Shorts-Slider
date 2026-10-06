import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[2] / '.github/scripts/check_sensitive_files.py'
SPEC = importlib.util.spec_from_file_location('sensitive_files', PATH)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class SensitiveFilesTest(unittest.TestCase):
    def test_private_paths_and_credentials(self):
        for name in ['keystore.properties', 'secret.jks', '.env.local', 'chat-google-antigravity/chat.db', 'backup_tv/archive.zip', 'original.zip', 'undo.json']:
            self.assertTrue(guard.private_path(name), name)
        for name in ['fork/mediaservice.patch', 'tools/configure_shorts.py']:
            self.assertFalse(guard.private_path(name), name)
        self.assertTrue(guard.SECRET.search(('ghp_' + 'a' * 40).encode()))
        self.assertFalse(guard.SECRET.search(b"storePassword = keystoreProperties['storePassword']"))

    def test_forced_staging_of_private_file_is_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run(['git', 'init', '-q', folder], check=True)
            path = Path(folder) / 'private.jks'
            path.write_bytes(b'synthetic fixture')
            subprocess.run(['git', '-C', folder, 'add', '-f', 'private.jks'], check=True)
            result = subprocess.run([sys.executable, str(PATH), '--staged'], cwd=folder, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(b'synthetic fixture', result.stderr)
