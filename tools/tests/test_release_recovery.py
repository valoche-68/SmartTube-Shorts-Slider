import base64
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[2] / '.github/scripts/release.py'
SPEC = importlib.util.spec_from_file_location('release_recovery', PATH)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class PublicationRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.assets = self.folder / 'release_assets'
        self.assets.mkdir()
        self.expected = {'a.apk': b'validated a', 'b.apk': b'validated b', 'build-info.json': b'validated provenance'}
        for name, content in self.expected.items():
            (self.assets / name).write_bytes(content)
        self.remote = {}
        self.calls = []
        self.fail_upload = None
        self.info = dict(tag='v32.56-stable-slider.2', source_commit='exact-source', upstream_tag='32.56s', channel='stable')

    def api(self, path):
        return {'assets': [{'name': name, 'state': 'uploaded'} for name in self.remote]}

    def gh(self, *args):
        self.calls.append(args)
        if args[:2] == ('release', 'download'):
            directory = Path(args[args.index('--dir') + 1])
            for name, content in self.remote.items():
                (directory / name).write_bytes(content)
        elif args[:2] == ('release', 'upload'):
            if self.fail_upload:
                self.fail_upload(args)
            else:
                path = Path(args[-1])
                self.remote[path.name] = path.read_bytes()
        return ''

    def publish(self, existing=None):
        if existing is None:
            existing = {'isDraft': True}
        with patch.object(release, 'api', side_effect=self.api), patch.object(release, 'gh', side_effect=self.gh), \
             patch.object(release, 'run'), patch.object(release, 'existing_release', return_value=existing), \
             patch.object(release, 'commit_metadata'):
            release.publish(self.folder, self.info, self.assets)

    def test_partial_matching_draft_resumes_only_missing_assets(self):
        self.remote['a.apk'] = self.expected['a.apk']
        self.publish()
        uploaded = [Path(args[-1]).name for args in self.calls if args[:2] == ('release', 'upload')]
        self.assertEqual(uploaded, ['b.apk', 'build-info.json'])
        self.assertEqual(self.remote, self.expected)
        self.assertTrue(any(args[:2] == ('release', 'edit') for args in self.calls))

    def test_422_after_success_is_accepted_only_after_exact_byte_verification(self):
        def completed_despite_error(args):
            self.remote.update(self.expected)
            raise subprocess.CalledProcessError(1, ['gh', 'release', 'upload'], stderr='HTTP 422 ReleaseAsset.name already exists')
        self.fail_upload = completed_despite_error
        self.publish()
        self.assertEqual(sum(args[:2] == ('release', 'upload') for args in self.calls), 1)
        self.assertTrue(any(args[:2] == ('release', 'edit') for args in self.calls))

    def test_lost_response_to_first_asset_continues_remaining_uploads(self):
        def first_response_lost(args):
            path = Path(args[-1])
            self.remote[path.name] = path.read_bytes()
            self.fail_upload = None
            raise subprocess.CalledProcessError(1, ['gh', 'release', 'upload'])
        self.fail_upload = first_response_lost
        self.publish()
        self.assertEqual(self.remote, self.expected)
        self.assertEqual(sum(args[:2] == ('release', 'upload') for args in self.calls), 3)
        self.assertTrue(any(args[:2] == ('release', 'edit') for args in self.calls))

    def test_upload_error_without_an_uploaded_asset_never_publishes(self):
        def failed_before_upload(args):
            raise subprocess.CalledProcessError(1, ['gh', 'release', 'upload'])
        self.fail_upload = failed_before_upload
        with self.assertRaises(subprocess.CalledProcessError):
            self.publish()
        self.assertFalse(any(args[:2] == ('release', 'edit') for args in self.calls))

    def test_unexpected_remote_asset_is_not_deleted_or_published(self):
        self.remote['unexpected.apk'] = b'unrelated'
        with self.assertRaisesRegex(RuntimeError, 'Unexpected'):
            self.publish()
        self.assertFalse(any(args[1] in ('edit', 'upload', 'delete') for args in self.calls))

    def test_same_name_with_different_bytes_is_rejected_without_clobber(self):
        self.remote['a.apk'] = b'different build'
        with self.assertRaisesRegex(RuntimeError, 'mismatch'):
            self.publish()
        self.assertFalse(any(args[1] in ('edit', 'upload', 'delete') for args in self.calls))

    def test_already_published_release_is_never_replaced(self):
        with self.assertRaisesRegex(RuntimeError, 'already published'):
            self.publish({'isDraft': False})
        self.assertEqual(self.calls, [])

    def test_unfinished_asset_is_rejected(self):
        with patch.object(release, 'api', return_value={'assets': [{'name': 'a.apk', 'state': 'starter'}]}):
            with self.assertRaisesRegex(RuntimeError, 'finished'):
                release.verify_remote_assets(self.info['tag'], self.assets, require_complete=False)


class AutomationDraftRecoveryTest(unittest.TestCase):
    def test_matching_retained_draft_build_is_not_removed_or_rebuilt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'release-build' / 'stable'
            assets = folder / 'release_assets'
            assets.mkdir(parents=True)
            tag = 'v32.56-stable-slider.' + str(release.CONFIG['revision'])
            records = [dict(file=arch + '.apk', sha256='validated', architectures=[arch]) for arch in release.ARCHES]
            info = dict(patch_sha256='patch', upstream_commit='source', tag=tag, apks=records)
            (assets / 'build-info.json').write_text(json.dumps(info))
            marker = folder / 'retained-build-marker'
            marker.write_text('keep')
            with patch.object(release, 'ROOT', root), patch.object(release, 'latest', return_value='32.56s'), \
                 patch.object(release, 'gh', return_value='source'), patch.object(release, 'patch_digest', return_value='patch'), \
                 patch.object(release, 'existing_release', return_value={'isDraft': True}), \
                 patch.object(release, 'state_read', return_value=({}, 'state-sha')), patch.object(release, 'state_write'), \
                 patch.object(release, 'verify_apk', side_effect=records) as verify, patch.object(release, 'publish') as publish, \
                 patch.object(release, 'prepare') as prepare, patch.object(release, 'build') as build:
                release.automate(['stable'], retry=True)
            self.assertTrue(marker.exists())
            prepare.assert_not_called()
            build.assert_not_called()
            self.assertEqual(verify.call_count, 4)
            publish.assert_called_once_with(folder, info, assets)


class StateRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.state = {'stable:source:patch': {'status': 'published'}}
        self.error = subprocess.CalledProcessError(1, ['gh', 'api'], stderr='unexpected end of JSON input')

    def test_lost_response_is_reconciled_without_a_duplicate_write(self):
        with patch.object(release, 'gh', side_effect=self.error) as gh, \
             patch.object(release, 'state_read', return_value=(self.state, 'new-sha')):
            release.state_write(self.state, 'old-sha')
        self.assertEqual(gh.call_count, 1)
        args = gh.call_args.args
        self.assertNotIn('--input', args)
        content = next(value.removeprefix('content=') for value in args if value.startswith('content='))
        self.assertEqual(json.loads(base64.b64decode(content)), self.state)

    def test_retry_uses_same_sha_when_server_state_has_not_changed(self):
        with patch.object(release, 'gh', side_effect=[self.error, 'success']) as gh, \
             patch.object(release, 'state_read', return_value=({}, 'old-sha')):
            release.state_write(self.state, 'old-sha')
        self.assertEqual(gh.call_count, 2)
        self.assertEqual(gh.call_args_list[0], gh.call_args_list[1])

    def test_concurrent_state_change_is_preserved(self):
        other = {'beta:new-source:patch': {'status': 'published'}}
        with patch.object(release, 'gh', side_effect=self.error) as gh, \
             patch.object(release, 'state_read', return_value=(other, 'concurrent-sha')):
            with self.assertRaisesRegex(RuntimeError, 'concurrently'):
                release.state_write(self.state, 'old-sha')
        self.assertEqual(gh.call_count, 1)

    def test_uncertain_writes_are_bounded_to_three_attempts(self):
        with patch.object(release, 'gh', side_effect=self.error) as gh, \
             patch.object(release, 'state_read', side_effect=RuntimeError('temporary read failure')):
            with self.assertRaisesRegex(RuntimeError, 'three attempts'):
                release.state_write(self.state, 'old-sha')
        self.assertEqual(gh.call_count, 3)


if __name__ == '__main__':
    unittest.main()
