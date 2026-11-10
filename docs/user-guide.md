# SmartTube Shorts Slider — user guide

[Home](../README.md) · **English** · [Français](user-guide.fr.md)

## Our version of SmartTube

This project provides a **custom APK**, separate from official SmartTube. It reuses native preferences but also changes Shorts recognition, identity retention and next-video selection. It is independent of the upstream developer.

**New-profile defaults:** up/down navigation, autoplay, the visible button and next-Short preparation are enabled. Updates preserve saved choices. **Our APK does not need the official-app configuration script.**

[Use Shorts and change the four settings →](manual-setup.md)

The button before **Quality** controls autoplay: ON advances through available Shorts; OFF repeats the current Short. It shares **Loop Shorts**. Hiding it does not change autoplay. Playback stops when no next Short is available; the button does not create an infinite feed.

Long portrait videos are not classified as Shorts solely by their shape. Player controls must be hidden for navigation shortcuts to act on videos.

## Next-Short preparation and speed

During playback, one request fetches formats and stream addresses for **one next Short**. Its result is separate from the current playback cache and history identifier. A ready, valid result can be used on navigation; otherwise normal playback starts without waiting for preparation.

Official SmartTube also prepares format information in some situations. Our modification concerns Shorts-specific triggering, isolated results and an option to disable preparation; preparation in general is not claimed as an exclusive feature.

**Speed improvements have not been measured.** The first Short can still take time to load; it is not prepared before opening it. There is no second decoder, fully downloaded next video or guaranteed ten-to-twenty-Short queue. Official buffers and pagination are retained.

## Official SmartTube

Native preferences exist in the reviewed sources, but the reported Fire TV trials did not reproduce the expected navigation and autoplay behavior. The tutorial and script are no longer presented as equivalent to our APK.

[Official-settings limitations and the script’s experimental status →](official-settings.md)

## Downloads and upgrades

[Latest stable](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest) · [Beta and all releases](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases)

**Guided PC installation:** [paste one ADB command](install.md) · [read the full script](../tools/install_slider.py). It installs our stable APK, detects the architecture and does not launch the app.

| APK | Choose according to the architectures supported by Android |
| --- | --- |
| `armeabi-v7a` | 32-bit ARM, common on Fire TV |
| `arm64-v8a` | 64-bit ARM |
| `x86` | Android x86 / compatible emulators |
| `universal` | Contains all three architectures above; larger download |

The hardware’s marketing name is not sufficient: a 64-bit device can run a 32-bit system. Check Android’s supported ABIs with `adb shell getprop ro.product.cpu.abilist`.

### Install and update

The Android package IDs are `org.smarttube.stable` and `org.smarttube.beta`. Shorts Slider updates use the release certificate listed below. An update with the same package ID and signature preserves data: **do not uninstall the app to update it**. Keep a recent backup.

### If you use the official app

Official APKs have the same package ID but a different signing key, so the same channel cannot coexist or be directly replaced. Official settings and the script are not a validated way to obtain Shorts Slider behavior; see [their limitations](official-settings.md).

If migrating, make a complete backup, copy it to your PC, check that the ZIP is readable and keep account files private. Download and verify the replacement APK before any uninstall. Debug-signed installations also require a separate migration; the project does not promise a direct update in that case. See the [migration guide](migration.md).

## Releases with traceable sources

- Two channels: stable and beta are built from their **exact official tags**, pinned submodules and versioned patches.
- The workflow checks every six hours and blocks publication on incompatible source changes; it never forces a merge from `master`.
- Identical failures are not repeatedly retried: a new source, patch revision or manual retry is required.
- Checks cover versions, package IDs, native architectures, signatures and update URLs before publication.
- Releases include `build-info.json`, `SHA256SUMS` and links to actual VirusTotal reports when available. **The workflow does not invent a clean score.**

### Signing certificate

SHA-256 fingerprint:

```text
80a1a2db29be237b85486957804c21ddfa1a6c0371b93f2bd293e134aa138838
```

Automatic publication does not guarantee compatibility with all future upstream changes. Device testing remains useful, especially for beta builds.

## Development and contributions

See [development documentation](development.md). Private keys, passwords, personal backups and conversation exports are excluded from Git and checked before commits and in CI. Backups may contain account credentials: do not attach them to issues or public reports.

[MIT license](../LICENSE). Based on [SmartTube by Yurii Liskov and contributors](https://github.com/yuliskov/SmartTube). Dependencies retain their own licenses.
