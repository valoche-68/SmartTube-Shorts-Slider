# Shorts transition diagnostic

[Home](../README.md) · **English** · [Français](shorts-performance-diagnostic.fr.md)

Status recorded on October 21, 2026: device trials of internal revision 3 revealed regressions despite its automated tests. The fix was ported to official stable 32.68 (tag `32.68s` and matching submodules) for validation; no speed improvement had been confirmed on a device.

## Logs and identified causes

Android logs were read without launching, stopping or controlling SmartTube. The latest capture covered about three minutes and contained 554 process lines. It showed a cache miss, followed by no foreground format lookup, received formats or preparation start. This absence matches the blockage found in code; it does not measure a twenty-second network delay. Raw files remain private, outside the repository.

Two controller defects explain the symptoms:

- The presenter assigns the new video **after** notifying controllers. Checking the current video’s identity during that notification therefore abandoned the request before sending it. Previous tests had already assigned the new video, hiding the defect.
- The subscription wrapper remained marked active after the format lookup completed. The end-of-playback check then blocked automatic advancement. Manual navigation used another path.

Two additional waits were removed: unfinished preparation is no longer transferred to the foreground, and a known Short no longer waits for section pagination before being offered.

## Restored playback path

Loading retains the complete 32.68 path, including authentication, client selection and Innertube fallback. Preparation runs it in a private service and cache. Only a completed, still-valid result can be activated; otherwise normal playback starts immediately. Preparation writes no history.

Results are delivered on the main thread after the presenter notification. A request generation invalidates old results during rapid changes. The controller keeps the actual subscription, whose completion can be observed by autoplay. Button OFF restores Shorts looping.

Preparation remains limited to the formats and addresses of one next video, with cancellation, validity checks and a delay before retrying after an error. Official video buffers remain unchanged.

`ShortsPreparation` traces distinguish ready, missing and pending cache states, normal lookup, received formats and playback readiness. They contain no video ID, stream URL, account or token.

## Validation

Tests now reproduce the actual `PlaybackPresenter.onNewVideo` ordering without assigning its current video in advance. They check loading, automatic advancement after format completion, looping with the button OFF, deferred activation of a ready cache and rapid changes. Service tests also check authentication, Innertube fallback and cache isolation.

Before the 32.68 port, all 61 common-module tests passed locally on the 32.56 base. Each defect was also reintroduced separately in temporary controller copies: each caused three real-lifecycle tests to fail. That evidence required additional tests against the exact 32.68 sources.

Sources and tests were compiled locally under JDK 17, then run with JUnit and Robolectric 4.11.1, simulated SDK 28, reusing other modules’ compiled classes. On 32.68, a complete Gradle run then passed **84 Android tests**: 68 common-module, 7 media-service and 9 SABR-player tests, with no failures. The **66 Python tests** also passed (9 Windows cases skipped on Linux). Fixes apply to the exact stable and beta tags, each with its own submodules. The [signed CI build](https://github.com/valoche-68/SmartTube-Shorts-Slider/actions/runs/39636698469), at code commit `7c02bc35e617e0801153a98fe342be1efd5a9541`, subsequently succeeded for both channels: **84 Android tests per channel**, eight checked APKs, the expected release signature, internal codes `245804` and official bases `32.68s` / `32.68`. All eight downloaded files, source archives and hashes were checked again locally. The [stable](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/tag/v32.68-stable-slider) and [beta](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/tag/v32.68-beta-slider) releases were then published at the user’s request with those same APKs and exact sources. OTA metadata and the stable compatibility manifest were updated. Previous releases and their custom tags were removed after verified private archiving. Fire TV playback testing and the speed comparison still needed confirmation. Automated test results do not measure Fire TV playback smoothness. Test counts here describe that validation run, not the current size of the test suite.

## Next device trial

ARMv7 stable `245804`, based on `32.68s`, was installed on Fire TV using `adb install -r`, without uninstalling or launching the app. The APK read back from the device matched the checked file. The UID and first-install time were unchanged; checking accounts and settings in the interface awaited the user’s next launch.

From Home, then another section: check several transitions, autoplay ON/OFF, rapid Down presses and returning with Up. Compare preparation enabled and disabled using trace durations. The first Short still requires normal loading. Describe a speed improvement only after that trial.
