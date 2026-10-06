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
        return {'isDraft': True, 'assets': [{'name': name, 'state': 'uploaded'} for name in self.remote]}

    def gh(self, *args):
        self.calls.append(args)
        if args[:2] == ('release', 'view'):
            return json.dumps(self.api('draft CLI'))
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
        with patch.object(release, 'api', side_effect=AssertionError('Draft lookup must use the CLI')), patch.object(release, 'gh', side_effect=self.gh), \
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

    def test_empty_draft_is_visible_through_cli_without_rest_tag_lookup(self):
        with patch.object(release, 'api', side_effect=AssertionError('REST tag endpoint hides drafts')), \
             patch.object(release, 'gh', return_value=json.dumps({'isDraft': True, 'assets': []})) as gh:
            self.assertEqual(release.verify_remote_assets(self.info['tag'], self.assets, require_complete=False), set())
        gh.assert_called_once_with('release', 'view', self.info['tag'], '--repo', release.REPO,
                                   '--json', 'assets,isDraft')

    def test_unfinished_asset_is_rejected(self):
        with patch.object(release, 'gh', return_value=json.dumps({'isDraft': True, 'assets': [{'name': 'a.apk', 'state': 'starter'}]})):
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
            info = dict(patch_sha256='patch', upstream_commit='source', upstream_tag='32.56s', channel='stable',
                        version_name='32.56-slider.' + str(release.CONFIG['revision']),
                        version_code=244600 + release.CONFIG['revision'], tag=tag, apks=records)
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


    def assert_missing_runner_recovery(self, existing):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'release-build' / 'stable'
            assets = folder / 'release_assets'
            target = 'v32.56-stable-slider.' + str(release.CONFIG['revision'])
            info = {'tag': target, 'source_commit': 'existing-immutable-commit'}
            with patch.object(release, 'ROOT', root), patch.object(release, 'latest', return_value='32.56s'), \
                 patch.object(release, 'gh', return_value='upstream-source'), patch.object(release, 'patch_digest', return_value='patch'), \
                 patch.object(release, 'existing_release', return_value=existing), \
                 patch.object(release, 'existing_tag_commit', return_value='existing-immutable-commit'), \
                 patch.object(release, 'state_read', return_value=({}, 'state-sha')), patch.object(release, 'state_write'), \
                 patch.object(release, 'recover_from_tag', return_value=info) as recover, \
                 patch.object(release, 'prepare') as prepare, patch.object(release, 'build', return_value=assets) as build, \
                 patch.object(release, 'publish') as publish:
                release.automate(['stable'], retry=True)
            recover.assert_called_once_with('stable', '32.56s', 'upstream-source', target, folder)
            prepare.assert_not_called()
            build.assert_called_once_with(folder, info)
            publish.assert_called_once_with(folder, info, assets)

    def test_lost_runner_draft_rebuilds_exact_existing_tag(self):
        self.assert_missing_runner_recovery({'isDraft': True})

    def test_tag_without_release_is_recovered_without_generating_a_new_source_commit(self):
        self.assert_missing_runner_recovery(None)


class ExactTagRebuildTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'recovered'
        self.tag = 'v32.56-beta-slider.' + str(release.CONFIG['revision'])
        self.info = dict(channel='beta', upstream_tag='32.56', upstream_commit='upstream-source',
                         tag=self.tag, patch_sha256='patch', media_commit='pinned-media',
                         version_name='32.56-slider.' + str(release.CONFIG['revision']),
                         version_code=244600 + release.CONFIG['revision'])
        self.commands = []
        self.head = 'existing-immutable-commit'
        self.parent = 'upstream-source'
        self.media = 'pinned-media'

    def git_run(self, *args, **kwargs):
        self.commands.append(args)
        if args[:2] == ('git', 'clone'):
            (self.folder / 'fork').mkdir(parents=True)
            (self.folder / 'MediaServiceCore').mkdir()
            (self.folder / 'fork/build.json').write_text(json.dumps(self.info))
        if args[:2] == ('git', 'rev-parse'):
            if kwargs.get('cwd') == self.folder / 'MediaServiceCore': return self.media
            return self.parent if args[2] == 'HEAD^' else self.head
        return ''

    def recover(self):
        with patch.object(release, 'ROOT', self.root), patch.object(release, 'patch_digest', return_value='patch'), \
             patch.object(release, 'existing_tag_commit', return_value='existing-immutable-commit'), \
             patch.object(release, 'run', side_effect=self.git_run), patch.object(release, 'configure_build_environment') as environment:
            info = release.recover_from_tag('beta', '32.56', 'upstream-source', self.tag, self.folder)
        return info, environment

    def test_rebuild_uses_existing_commit_pinned_submodule_and_media_patch_without_new_commit(self):
        info, environment = self.recover()
        self.assertEqual(info['source_commit'], 'existing-immutable-commit')
        self.assertTrue(any(command[:3] == ('git', 'submodule', 'update') for command in self.commands))
        self.assertEqual(sum(command[:2] == ('git', 'apply') for command in self.commands), 2)
        self.assertFalse(any(command[1] in ('commit', 'push', 'tag') for command in self.commands))
        environment.assert_called_once_with(self.folder)

    def test_different_patch_digest_stops_recovery_before_signing(self):
        self.info['patch_sha256'] = 'different-code'
        with self.assertRaisesRegex(RuntimeError, 'different sources'):
            self.recover()
        self.assertFalse(any(command[:2] == ('git', 'apply') for command in self.commands))

    def test_tag_changed_during_fetch_is_rejected(self):
        self.head = 'changed-tag'
        with self.assertRaisesRegex(RuntimeError, 'changed during'):
            self.recover()

    def test_wrong_upstream_parent_is_rejected(self):
        self.parent = 'other-upstream-source'
        with self.assertRaisesRegex(RuntimeError, 'based directly'):
            self.recover()

    def test_wrong_pinned_media_submodule_is_rejected(self):
        self.media = 'different-media'
        with self.assertRaisesRegex(RuntimeError, 'unexpected media'):
            self.recover()

    def test_local_partial_build_is_preserved_for_inspection(self):
        self.folder.mkdir()
        marker = self.folder / 'existing'
        marker.write_text('keep')
        with self.assertRaisesRegex(RuntimeError, 'incomplete local build'):
            self.recover()
        self.assertEqual(marker.read_text(), 'keep')
        self.assertEqual(self.commands, [])


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
