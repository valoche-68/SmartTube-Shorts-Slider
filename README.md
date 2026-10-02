# SmartTube Shorts Slider

Shorts on TV: native settings or a dedicated autoplay button.

**English** · [Français](README.fr.md)

## 🎛️ Keep official SmartTube

Shorts navigation and autoplay are already built in. Our assistant helps configure them through a backup you restore on your TV.

Install [Python 3.10+](https://www.python.org/downloads/) and [ADB](https://developer.android.com/tools/releases/platform-tools), connect your TV, then paste:

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh
```

**Windows — PowerShell**

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content))
```

French menus · Official **32.56 stable/beta** · No player button added.

[Setup, manual settings & undo →](docs/user-guide.md#official-smarttube)

## ▶️ Shorts Slider — our version of SmartTube

A custom SmartTube APK with two additions for Shorts:

- **Autoplay button in the player:** ON advances, OFF loops. Show or hide it in settings.
- **Next-Short preparation:** fetches the next Short’s playback details ahead of time. Can be disabled.

**On a new profile:** up/down navigation and autoplay are enabled, the button is visible and next-Short preparation is on. All options remain adjustable; updates preserve your choices.

**[Download stable](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest)** · **[Beta & all releases](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases)**

[Installation, settings & APK choices →](docs/user-guide.md#shorts-slider)

*Fire TV testing and speed measurements are still pending.*

---

Based on [SmartTube](https://github.com/yuliskov/SmartTube) · [Build & maintenance](docs/development.md) · [MIT](LICENSE)
