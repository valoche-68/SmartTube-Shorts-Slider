import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


release = module('release_media_selection', ROOT / '.github/scripts/release.py')
media = module('apply_media_selection', ROOT / 'fork/apply_media_patch.py')
CONFIG = dict(media_base_commit='stable-source', media_beta_base_commit='beta-source')


class MediaPatchSelectionTest(unittest.TestCase):
    def test_channel_and_pinned_submodule_select_matching_patch(self):
        with patch.object(release, 'CONFIG', CONFIG):
            self.assertEqual(release.media_patch_name('stable'), 'mediaservice.patch')
            self.assertEqual(release.media_patch_name('beta'), 'mediaservice-beta.patch')
        self.assertEqual(media.patch_for_head(CONFIG, 'stable-source'), 'mediaservice.patch')
        self.assertEqual(media.patch_for_head(CONFIG, 'beta-source'), 'mediaservice-beta.patch')
        with self.assertRaisesRegex(RuntimeError, 'Unknown media'):
            media.patch_for_head(CONFIG, 'unreviewed-source')
        with self.assertRaisesRegex(RuntimeError, 'Unknown release channel'):
            release.prepare('nightly', '32.68', Path('unused'))

    def test_old_shared_base_config_retains_original_patch_and_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'fork').mkdir()
            contents = [b'app', b'media', b'legacy config']
            for name, content in zip(['shorts.patch', 'mediaservice.patch', 'config.json'], contents):
                (root / 'fork' / name).write_bytes(content)
            config = dict(media_base_commit='same-source')
            with patch.object(release, 'ROOT', root), patch.object(release, 'CONFIG', config):
                self.assertEqual(release.media_patch_name('beta'), 'mediaservice.patch')
                self.assertEqual(release.patch_digest(), hashlib.sha256(b''.join(contents)).hexdigest())
            self.assertEqual(media.patch_for_head(config, 'same-source'), 'mediaservice.patch')

    def test_digest_includes_each_configured_media_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'fork').mkdir()
            for name in ['shorts.patch', 'mediaservice.patch', 'mediaservice-beta.patch', 'config.json']:
                (root / 'fork' / name).write_text(name)
            with patch.object(release, 'ROOT', root), patch.object(release, 'CONFIG', CONFIG):
                original = release.patch_digest()
                for name in ['mediaservice.patch', 'mediaservice-beta.patch']:
                    path = root / 'fork' / name
                    path.write_text('changed ' + name)
                    self.assertNotEqual(release.patch_digest(), original)
                    path.write_text(name)
                (root / 'fork/mediaservice-beta.patch').unlink()
                with self.assertRaises(FileNotFoundError): release.patch_digest()

    def test_local_apply_is_idempotent_and_refuses_unreviewed_heads_before_applying(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'fork').mkdir()
            (root / 'fork/config.json').write_text(json.dumps(CONFIG))
            for head, expected in [('stable-source', 'mediaservice.patch'), ('beta-source', 'mediaservice-beta.patch')]:
                with self.subTest(head=head), patch.object(media, 'ROOT', root), \
                     patch.object(media.subprocess, 'check_output', return_value=head + '\n'), \
                     patch.object(media.subprocess, 'run', side_effect=[SimpleNamespace(returncode=1),
                                                                        SimpleNamespace(returncode=0),
                                                                        SimpleNamespace(returncode=0)]) as run:
                    media.main()
                    self.assertEqual(run.call_count, 3)
                    self.assertEqual(run.call_args_list[-1].args[0][-1], str(root / 'fork' / expected))
                with patch.object(media, 'ROOT', root), \
                     patch.object(media.subprocess, 'check_output', return_value=head), \
                     patch.object(media.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
                    media.main()
                    self.assertEqual(run.call_count, 1)
            with patch.object(media, 'ROOT', root), \
                 patch.object(media.subprocess, 'check_output', return_value='unknown'), \
                 patch.object(media.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'Unknown media'): media.main()
                run.assert_not_called()
