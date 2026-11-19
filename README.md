# SmartTube Shorts Slider

Our version of SmartTube for navigating Shorts and controlling automatic playback on TV.

**English** · [Français](README.fr.md)

## ▶️ What our APK changes

- **Autoplay button before Quality:** ON advances through available Shorts; OFF repeats the current Short. The button can be hidden.
- **Shorts navigation:** changes to recognition and next-video selection, including Shorts opened from Home. Native shortcuts remain adjustable.
- **Next-Short preparation:** fetches playback information for one next Short into a separate cache. Optional; no measured speed improvement is guaranteed.

**Already enabled for new profiles:** up/down navigation, autoplay, the player button and next-Short preparation. Updates preserve existing choices.

**[Download our stable APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest)** · [Beta](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases)

[Using and configuring Shorts Slider →](docs/manual-setup.md) · [Installation and updates →](docs/user-guide.md#downloads-and-upgrades)

## 📲 Install our APK with ADB

Paste one command on your PC: it checks Python and ADB, installs missing prerequisites on supported systems, then guides you through installing **stable Shorts Slider** on your TV. Your system may request permission. The app is not launched after installation.

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh
```

**Windows — PowerShell**

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content))
```

[Installation walkthrough →](docs/install.md) · [Read the full script →](tools/install_slider.py)

*Fire TV testing is in progress. The first Short can still take time to load; preparing the next Short does not prepare that initial startup.*

---

Based on [SmartTube](https://github.com/yuliskov/SmartTube) · [Build & maintenance](docs/development.md) · [MIT](LICENSE)
