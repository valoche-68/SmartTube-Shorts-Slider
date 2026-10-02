# SmartTube Shorts Slider

**Shorts on TV, with the settings that suit you.**

**English** · [Français](README.fr.md) · [Releases](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases) · [Official SmartTube](https://github.com/yuliskov/SmartTube)

[![Validation](https://github.com/valoche-68/SmartTube-Shorts-Slider/actions/workflows/CI.yml/badge.svg)](https://github.com/valoche-68/SmartTube-Shorts-Slider/actions/workflows/CI.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Choose between configuring the official app or installing this independently maintained edition for its player button and next-Short preparation.

## 1. Keep official SmartTube

Shorts navigation and automatic playback already exist:

- **Settings → General → Key remapping:** choose Shorts navigation with up/down or left/right, or disable those shortcuts.
- **Settings → Video player → Misc:** turn off “Loop Shorts” and select the playback mode that advances to the next video.
- Optionally enable “Use current section content as playlist”. The global playback mode also affects regular videos.

The [guided configuration tool](docs/configuration-native.md) runs with Python 3.10+ and ADB on Linux, macOS and Windows:

```sh
python3 tools/configure_shorts.py
```

On Windows use `tools\configure_shorts.cmd`. It modifies a recent official backup, retains the original, and lets you restore it through SmartTube's own interface. No root, uninstall or replacement APK is involved. You can inspect settings, choose navigation, configure automatic playback and the section playlist, preview changes, and selectively undo them using a fresh backup.

The verified source schema is official **32.56 stable and beta**. Unknown versions are rejected. End-to-end Fire TV validation remains pending. The tool does **not** add the player button or speculative preparation. Manual settings remain an option.

## 2. Use the custom APK

| Feature | Official app | Shorts Slider |
| --- | --- | --- |
| Up/down and left/right navigation | Native settings | Same settings, up/down enabled for new profiles |
| Automatic Shorts playback | Native settings | Enabled for new profiles, with a player toggle |
| Button before Quality | Not included | Shorts only; can be hidden |
| Our next-Short preparation | Not included | Enabled by default; can be disabled |
| Video buffers and pagination | Upstream behavior | Upstream behavior retained |

The button shares the native Loop Shorts preference: **ON advances; OFF loops the current Short**. Hide it in **Video player → Player buttons**, independently of automatic playback. Disable preparation in **Video player → Misc**. Existing choices survive upgrades. Long portrait videos are not classified as Shorts merely from their shape. Automatic Shorts playback stops when no next Short is available.

Preparation fetches playback formats and stream addresses for **one next Short**, using a separate result cache and playback-history context. It does not download an entire video, run a second decoder, or maintain ten to twenty ready-to-play Shorts. **The speed benefit has not yet been measured on the maintainer's Fire TV.** Device, network and YouTube behavior affect results.

## Downloads and upgrades

[Latest stable](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest) · [Beta and all releases](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases)

Available APKs: `armeabi-v7a`, `arm64-v8a`, `x86`, and a universal package containing those three native architectures. Check Android's supported ABIs with `adb shell getprop ro.product.cpu.abilist`; the hardware's marketing name is not sufficient.

The Android package IDs are `org.smarttube.stable` and `org.smarttube.beta`. Shorts Slider updates use the release certificate listed below. An update with the same package ID and signature preserves data: **do not uninstall the app to update it**. Keep a recent backup.

Official APKs use a different signing key, so the same channel cannot coexist or be directly replaced. Prefer native settings first. If migrating, make a complete backup, copy it to your PC and verify it before any uninstall; download and verify the replacement APK first. Debug-signed installations also require a separate migration. See the [migration guide](docs/migration.md).

Fork certificate SHA-256:

```text
80a1a2db29be237b85486957804c21ddfa1a6c0371b93f2bd293e134aa138838
```

## Releases with traceable sources

Stable and beta are built from their exact official tags and pinned submodules, with reviewed patches. The workflow checks every six hours and stops on incompatible source changes or failed checks. Identical failures are not repeatedly retried. Automatic checks validate versions, package IDs, native architectures, signatures and update URLs.

Releases include `build-info.json` and `SHA256SUMS`. VirusTotal links lead to actual reports; the workflow does not invent a clean score. These checks do not replace device testing or guarantee future upstream compatibility.

See [development documentation](docs/development.md). Credentials, private keys, personal backups and conversation exports must remain outside Git and public reports.

[MIT license](LICENSE). Based on [SmartTube by Yurii Liskov and contributors](https://github.com/yuliskov/SmartTube). Dependencies retain their own licenses.
