# Install Shorts Slider from a PC

[Home](../README.md) · **English** · [Français](install.fr.md)

This assistant installs **our SmartTube Shorts Slider APK**, stable by default. It does not configure official SmartTube. The launcher checks Python 3.10+ and ADB and can install missing prerequisites. The menus are in French.

## 1. Prepare your TV

Connect your PC and TV to the same local network, enable **ADB debugging** in the TV’s developer options and find its IP address. Keep a recent backup before an update.

Devices using Android wireless pairing require `adb pair IP:PORT` first; then use the connection address and port displayed by the TV. See the [ADB documentation](https://developer.android.com/tools/adb).

## 2. Paste one command

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh
```

**Windows — PowerShell**, not Command Prompt

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content))
```

No Git clone is required. Working Python and ADB installations are reused; missing prerequisites are installed through your Linux package manager, Homebrew on macOS or WinGet on Windows. Homebrew is installed if needed. Your system may ask for approval or an administrator password. Do not run the whole command with `sudo`.

Linux/macOS need `curl` to start. If WinGet is missing on Windows, the launcher provides App Installer instructions and stops. It does not change PowerShell execution policy.

## 3. Follow the assistant

1. If no device is connected, enter the TV’s IP. The default port is `5555`; use `IP:PORT` for a different port.
2. Accept **Allow USB debugging** on the TV if prompted, then return to the terminal. If the connection fails first, check the address and debugging setting and rerun.
3. Select the TV if several devices are connected. The assistant displays the device, version and architecture supported by Android.
4. It downloads our APK from **this repository’s releases**, verifies its size and SHA-256 against published metadata, and requests confirmation. Enter **o** to install.
5. Wait for **Installation vérifiée. Application non lancée.** Open Shorts Slider yourself when ready.

Stable is the default. An identical version is left alone; downgrades are rejected. Temporary files are removed, while Python and ADB remain installed on the PC.

## Updates and existing accounts

The installer uses `adb install -r` without uninstalling. Android requires a compatible signature to update the app; an accepted update retains its data. The installer confirms the version and, when available, the UID and first-install time. It does not sign in or read account credentials.

**If official SmartTube or an incompatible variant occupies the same channel, the installer stops.** It never uninstalls, bypasses signatures or promises automatic account migration. See the [migration guide](migration.md) before changing signing keys.

Replacing an app may stop its running process. Install at a convenient time. The assistant never launches the app afterward.

## Optional arguments

Append these to the copied command:

| Argument | Effect |
| --- | --- |
| `--connect 192.168.1.50` | Use your TV’s IP directly; replace this example |
| `--device ID` | Select an already-connected ADB device |
| `--channel beta` | Install our beta instead of stable |
| `--dry-run` | Inspect device and release information without downloading or installing the APK |
| `--download-only` | Download and verify an APK on the PC without ADB; universal by default |
| `--download-only --arch armeabi-v7a` | Choose an architecture for a download-only operation |
| `--yes` | Skip installation confirmation; requires an unambiguous device |
| `--help` | Show help |

With a local checkout, use `sh tools/start.sh`, `tools/start.ps1` in PowerShell, or `python3 tools/install_slider.py` if prerequisites are already installed.

## Read all the code

[Full Python installer](../tools/install_slider.py) · [Linux/macOS launcher](../tools/start.sh) · [Windows launcher](../tools/start.ps1)

Automated tests use fake ADB devices. A real download can be verified separately with `--download-only`; this is not an installation test on every TV model.
