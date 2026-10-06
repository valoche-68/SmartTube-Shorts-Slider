#!/usr/bin/env python3
"""Refresh the public source patches; review diffs and bump config revision before publishing."""
import json
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[1]
config = json.loads((root / 'fork/config.json').read_text())
paths = [
 'common/build.gradle',
 'common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/data/Video.java',
 'common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/data/SimpleMediaItem.java',
 'common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/playback/controllers/PlayerUIController.java',
 'common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/playback/controllers/VideoLoaderController.java',
 'common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/playback/controllers/SuggestionsController.java',
 'common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/presenters/settings/PlayerSettingsPresenter.java',
 'common/src/main/java/com/liskovsoft/smartyoutubetv2/common/prefs/PlayerTweaksData.java',
 'common/src/main/java/com/liskovsoft/smartyoutubetv2/common/misc/NextVideoPreloader.java',
 'common/src/main/res/drawable-nodpi/action_shorts_auto_scroll.png',
 'common/src/main/res/values-fr/strings.xml', 'common/src/main/res/values/strings.xml', 'common/src/main/res/values/ids.xml',
 'common/src/test/java/com/liskovsoft/smartyoutubetv2/common/misc/NextVideoPreloaderTest.java',
 'common/src/test/java/com/liskovsoft/smartyoutubetv2/common/misc/ShortsPreferencesTest.java',
 'common/src/test/java/com/liskovsoft/smartyoutubetv2/common/misc/VideoShortsClassificationTest.java',
 'common/src/test/java/com/liskovsoft/smartyoutubetv2/common/misc/ShortsNavigationTest.java',
 'common/src/test/java/com/liskovsoft/smartyoutubetv2/common/misc/PlaybackNonceIsolationTest.java',
 'smarttubetv/src/main/java/com/liskovsoft/smartyoutubetv2/tv/ui/playback/actions/ShortsAutoScrollAction.java',
 'smarttubetv/src/main/java/com/liskovsoft/smartyoutubetv2/tv/ui/playback/other/VideoPlayerGlue.java',
 'smarttubetv/src/main/java/com/liskovsoft/smartyoutubetv2/tv/ui/mod/leanback/playerglue/tweaks/MaxControlsVideoPlayerGlue.java'
]
# Fail rather than accidentally include an unrelated file or credential.
for path in paths:
    if not (root / path).is_file(): raise SystemExit('Missing reviewed source: ' + path)
subprocess.run(['git', '-C', str(root), 'add', '-N', '--', *paths], check=True)
patch = subprocess.check_output(['git', '-C', str(root), 'diff', '--binary', config['base_commit'], '--', *paths])
(root / 'fork/shorts.patch').write_bytes(patch)
media = root / 'MediaServiceCore'
new_media = ['youtubeapi/src/main/java/com/liskovsoft/youtubeapi/app/PlaybackNonceState.java',
             'youtubeapi/src/main/java/com/liskovsoft/youtubeapi/service/PreparedShort.java',
             'youtubeapi/src/test/java/com/liskovsoft/youtubeapi/common/models/gen/ShortsIdentityTest.kt']
subprocess.run(['git', '-C', str(media), 'add', '-N', '--', *new_media], check=True)
patch = subprocess.check_output(['git', '-C', str(media), 'diff', '--binary', config['media_base_commit'], '--',
                                 'youtubeapi/src/main/java', new_media[-1]])
(root / 'fork/mediaservice.patch').write_bytes(patch)
print('Reviewed patch files refreshed.')
