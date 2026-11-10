# Build and maintenance

[Home](../README.md) · **English** · [Français](development.fr.md)

## Repository layout

`main` contains the fork’s development code, documentation, ADB installer, experimental official-settings tool and automation. Published APKs are built in a separate checkout of the exact official tag: a channel name is never used to arbitrarily label code from `master`.

- `fork/config.json`: upstream repository, comparison base, fork revision and expected public certificate fingerprint.
- `fork/shorts.patch`: application changes and tests.
- `fork/mediaservice.patch` and `fork/mediaservice-beta.patch`: the same isolated preparation, adapted to each channel’s pinned official submodules.
- `fork/build.json` in each published tag: build provenance. The release’s `build-info.json` adds the final source commit and APK hashes.

The tag’s media submodule stays pinned to the official commit. Apply its public patch before compiling:

```sh
git submodule update --init --recursive
python3 fork/apply_media_patch.py
```

Both media patches are included in every published tag; there is no dependency on a private submodule commit. The local script selects the patch based on the official media commit and rejects unknown commits. Stable and beta 32.71 pin the same media commit; both patches retain isolated next-Short preparation and the upstream client-selection API.

## Development

Install JDK 17, Android SDK 34, build-tools 30.0.3 and NDK 21.0.6113669. Configure `local.properties` or `ANDROID_HOME`. Never commit `keystore.properties`, a key or a password. Enable the local hook and run checks with:

```sh
git config core.hooksPath .githooks
python3 .github/scripts/check_sensitive_files.py
python3 -m unittest discover -s tools/tests -v
bash gradlew :common:testStstableDebugUnitTest \
  --tests '*ShortsPreferencesTest' --tests '*NextVideoPreloaderTest' --tests '*PlaybackNonceIsolationTest' \
  --tests '*VideoShortsClassificationTest' --tests '*ShortsNavigationTest' --tests '*SuggestionsControllerTest' \
  --tests '*PreparationStrategyTest' --tests '*ShortsPreparationLifecycleTest' \
  :youtubeapi:testStstableDebugUnitTest --tests '*ShortsIdentityTest' \
  :exoplayer-library-sabr:testStstableDebugUnitTest --tests '*SabrCdnSelectorTest'
```

The common module pins Robolectric to 4.11.1 for these tests under JDK 17; the previous 4.6.1 version cannot instrument Java 17 classes.

After changing the application or submodule, **increment the release revision**, run `python3 fork/update_patches.py`, then review the application patch and both media-channel patches. Application patch generation uses an explicit list of public files. Do not make general video-engine changes without specific validation.

Covered behavior includes preference migration, consistent native preferences, independently hiding the button, deduplicated and cancellable preparation requests, single-use cache entries, expiration and an isolated history context. Navigation tests also check Shorts identity retention, mixed lists without a section playlist, end-of-list behavior and cancellation of late responses. Preparation reuses the format provider in a separate instance; normal playback keeps its own fallbacks if preparation fails.

## Reproduce a release from the main repository

```sh
python3 .github/scripts/release.py prepare --channel stable --tag 32.71s --folder /new/path/build-stable
python3 .github/scripts/release.py build --channel stable --folder /new/path/build-stable
```

Preparation requires either the local signing configuration ignored by Git, or the `SIGNING_KEY` (base64), `KEY_STORE_PASSWORD`, `ALIAS` and `KEY_PASSWORD` environment variables. The key must match the configured public fingerprint. After building, APK checks cover the package, internal version, signature, native libraries and compiled update URLs.

An official version code `N` and fork revision `R` produce `N * 100 + R`, with `1 ≤ R < 100`. For example, 2461 and revision 5 produce 246105. The corresponding tags are `v32.71-stable-slider` and `v32.71-beta-slider`. The revision remains in internal APK metadata for updates; it does not appear in the tag, download filenames or release presentation. Visible titles remain “SmartTube Shorts Slider 32.71 — stable” and “SmartTube Shorts Slider 32.71 — beta”. Never replace binaries for an already published tag; increment the revision.

## GitHub automation

The `release-shorts-slider.yml` workflow runs every six hours or manually. It checks official releases, ignores announcements and aliases, selects each exact tag, initializes submodules, applies patches, runs tests and builds APKs. Signing secrets do not appear in interpolated commands or published files.

Publication uses a draft whose files are downloaded and compared before it becomes public. The tag points to the compiled source commit. OTA metadata changes only after verified publication. The stable manifest is also available under the `smarttube_stable2.json` alias.

The `.github/release-state.json` file on `main` records results by channel, official commit and patch digest. No separate automation branch is needed. An identical failure is skipped on later runs. To retry, run manually with `retry=true`. If an upload response is lost, existing files are reconciled by name and bytes, then missing files are uploaded. The complete set is required before publication.

After an interruption, keep the draft and its tag. Read uploaded files with `gh release view`, which supports drafts. A rerun can reuse `release-build/<channel>` after checking sources, signatures and architectures. If the runner is gone, it rebuilds from the existing tag’s exact commit after verifying provenance and submodules; the tag and application code remain unchanged. An incomplete local build is kept for inspection. Already-uploaded files must match the rebuilt bytes; any mismatch blocks resumption. No draft or tag is automatically deleted. Published APKs are not replaced. Verified release files are also kept for 30 days as GitHub Actions artifacts, including after failure, without private signing material. A metadata-publication failure can be repaired by a rerun that verifies the existing release’s sources. An uncertain state-write response is checked by rereading, with at most three attempts; a different concurrent state is preserved. Before writing OTA metadata, each publication fast-forwards to the latest `main` commits to retain state recorded between the two channels. A change limited to the state file does not rerun Android validation.

Test reports are kept for 30 days in Actions artifacts. No workflow immediately deletes all logs. VirusTotal is separate from build provenance: if a key is configured, the action submits APKs, then adds only links to actual reports.

## Experimental official-settings script

The script is not a validated alternative to the Shorts Slider APK. Reported official-app trials did not reproduce the expected behavior. Synthetic tests validate only preferences and backups; see [this approach’s status](official-settings.md).

Before accepting a new official version, compare its `PlayerTweaksData`, `PlayerData`, `GeneralData`, `AppPrefs` and `SharedPreferencesBase` preferences with the supported versions. Validate encoding, indices, defaults and restoration, then add the version to the script’s compatibility table and documentation. APK automation must not silently expand the script’s compatibility.

## Device validation

Software tests and APK inspection do not replace Fire TV testing. Check updates without uninstalling, preserved preferences, the hidden/visible button, long portrait videos, end-of-list behavior and the script’s backup/edit/restore workflow. Full device validation remains incomplete.

Compare transitions with preparation enabled and disabled on the same device and network; report the procedure and measurements before making numerical claims. Do not publish logs containing signed stream URLs, accounts or tokens.

The [Shorts transition diagnostic](shorts-performance-diagnostic.md) documents the limits of existing logs and preparation-lifecycle fixes.
