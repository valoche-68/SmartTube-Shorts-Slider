# Official assistant — experimental backup tool

[Home](../README.md) · **English** · [Français](configuration-native.fr.md)

**This script is not offered as a validated alternative to Shorts Slider.** It edits preferences in an official backup; it does not fix Shorts recognition or the player’s behavior. Reported official-app trials did not reproduce the expected result. Synthetic tests prove value changes and selective undo, not navigation or autoplay on TV. The complete restoration workflow remains unvalidated.

**Do not use this assistant for our APK:** its options are already enabled on a new profile and can be changed in settings. Follow the [Shorts Slider guide](manual-setup.md). See [the official app’s limitations](official-settings.md) for the difference.

The following commands are kept for deliberate experiments with the backup tool. They do not add the fork’s button or preparation handling, install an APK or require root on the TV. The assistant’s menus are in French.

## Automatic prerequisite installation

The command below checks **Python 3.10+** and **ADB**, reuses working tools and installs only missing prerequisites:

| System | Installation method |
| --- | --- |
| Linux | `apt-get`, `dnf`, `pacman`, `zypper` or `apk`, using packages from configured repositories |
| macOS | [Homebrew](https://docs.brew.sh/Installation), installed from its official source if missing; Python and [Android Platform Tools](https://formulae.brew.sh/cask/android-platform-tools) |
| Windows | [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/install), with `Python.Python.3.13` and `Google.PlatformTools`, for the current user |

The system may request confirmation or an administrator password. On Linux, only package-manager calls use `sudo` when needed. Homebrew may also request Apple’s developer tools. **Do not run the entire command with `sudo`.**

Linux/macOS require `curl`. If WinGet is missing on Windows, the launcher explains how to install [Microsoft App Installer](https://apps.microsoft.com/detail/9nblggh4nns1), then stops. Unsupported package managers, unavailable packages or a Python version that remains too old also cause it to stop. You can install [Python](https://www.python.org/downloads/) and [ADB](https://developer.android.com/tools/releases/platform-tools) manually, then rerun.

Prerequisites are checked again after installation. Help (`--help`) and local-backup operations (`--backup`) require Python but do not install ADB. Installed tools remain on the PC for future runs.

## Start without manually downloading a file

Paste **one command** into your terminal:

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh --official-settings
```

**Windows — PowerShell**

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content)) --official-settings
```

The explicit `--official-settings` mode is required: without it, the launcher installs our APK. The command retrieves the launcher from this repository. After checking and, if needed, installing prerequisites, it downloads `configure_shorts.py` into a temporary folder. The menu keeps access to keyboard input. A failed download never executes an incomplete file. The temporary folder is removed on exit without removing private backups. Git is not required; PowerShell execution policy is unchanged.

Append `--help` for help or `--channel beta` for the beta channel. Other script options work the same way.

With a local checkout, `sh tools/start.sh --official-settings` or `& ([scriptblock]::Create((Get-Content -Raw .\tools\start.ps1))) --official-settings` provides the same prerequisite installation. To run only the local script with prerequisites already installed:

```sh
python3 tools/configure_shorts.py
# Linux / macOS: tools/configure_shorts.sh
# Windows: tools\configure_shorts.cmd
```

## Connect the TV

Enable ADB debugging in the TV’s developer options, connect the PC and accept the prompt on the TV. Depending on the device, use `adb connect ADDRESS:PORT` or `adb pair`. The [Android documentation](https://developer.android.com/tools/adb) describes these modes. Do not expose ADB to the Internet.

If ADB was just installed, open a new terminal before using `adb connect`. With Homebrew, follow its instructions to add tools to `PATH` if needed. If the assistant finds no connected device, connect the TV and rerun; existing prerequisites will not be reinstalled.

## Guided workflow

1. The script checks the installed version. The preference formats reviewed in source are **32.68 stable and beta (Android code 2458)** and **32.56 stable and beta (2446)**. This does not validate player behavior or the complete TV workflow. Unknown versions are rejected; read [this approach’s limitations](official-settings.md) before proceeding. Our APK’s guide does not validate official-app settings.
2. Create a **new complete backup** under Settings → Backup/restore → Local backup. Give the script the ZIP’s full path shown on the TV. Locations vary by Android version; an old backup is never silently selected.
3. Choose navigation, autoplay and section-playlist settings, or inspect current values. The active profile is used; `--profile NAME` selects an existing profile.
4. Read the summary. Enabling autoplay disables Shorts looping and may select the global “next video” playback mode, which also affects long videos.
5. The script keeps `original.zip`, creates `configured.zip` and writes `undo.json` in a new private folder on the PC.
6. It offers to transfer the ZIP and open the official import interface. **Confirm restoration on the TV**, then reopen the app. SmartTube stopping after restoration is normal. Check the settings.
7. Return to the terminal after restoration to remove the temporary ZIP from the TV. The PC’s private folder remains available for undo.

Do not change other settings between backup and restoration: the official import restores an entire backup, even if the script edited only a few values.

## Work with a ZIP already copied to the PC

```sh
# Inspect settings without changing the TV
python3 tools/configure_shorts.py --backup backup.zip --version 32.68 --status

# Dry run: no files created, no transfer, no restoration
python3 tools/configure_shorts.py --backup backup.zip --version 32.68 \
  --navigation up-down --autoplay on --section on --dry-run

# Prepare the ZIP for manual import
python3 tools/configure_shorts.py --backup backup.zip --version 32.68 \
  --navigation up-down --autoplay on --section on --output ./private_shorts_backup
```

`--navigation left-right` selects left/right; `off` disables these shortcuts. `--autoplay off` restores Shorts looping. In non-interactive mode, omitted options leave their settings unchanged.

Import the configured ZIP with the TV’s file manager, or transfer it to SmartTube’s media folder and open it with the official import interface. If Android refuses the transfer or import, success is not reported: use the manual backup/restore workflow.

## Undo changes

First create a **new backup** of the current state, then run:

```sh
python3 tools/configure_shorts.py --backup current_backup.zip --version 32.68 \
  --undo /private/path/undo.json
```

The script restores the previous targeted values and keeps other settings from the new backup. If a targeted value has since been changed by another method, it stops rather than overwriting it. `original.zip` remains a complete emergency backup of the initial state.

## Private data and limitations

Backups may contain account credentials. The script does not send them to an external service or display them. Outputs are created under the user’s home directory, with restricted permissions where supported. On Windows, keep these files in your protected user folder; Unix permission modes do not replace Windows permissions.

Do not attach backups or undo logs to GitHub issues. Ambiguous archives, unsafe paths, unknown preferences and custom-app backups are rejected. Supporting a future version requires checking its official schema.
