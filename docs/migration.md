# Update or change signing keys

[Home](../README.md) · **English** · [Français](migration.fr.md)

## Update SmartTube Shorts Slider

Download the new stable or beta matching the installed channel. Check `SHA256SUMS` and the certificate fingerprint in the [user guide](user-guide.md#signing-certificate). Keep a recent backup outside the TV.

An update with the same package ID and signing key installs without uninstalling:

```sh
adb install -r /path/to/APK.apk
```

If Android reports an incompatible signature or a lower version code, stop and identify the installed version. Do not automatically add an uninstall or a downgrade bypass.

## Official app or debug build

A different signing key prevents a direct update. Shorts Slider keeps the official package IDs: it cannot coexist with the official app on the same channel.

1. Identify the currently installed channel and signing key. The Shorts Slider installer rejects incompatible variants; official settings do not migrate an installation to our APK.
2. If you choose Shorts Slider, create a recent complete backup in the currently installed app.
3. Copy the ZIP to the PC, outside the app’s storage, check that it is readable and keep a copy. Do not assume a backup on the TV will survive uninstallation.
4. Download the target APK and check its architecture, SHA-256 and signature **before** removing the previous app.
5. Only after these checks, uninstall the app with the different signature, install the new APK and restore the backup through the official interface.
6. Check settings and accounts. Some sessions may require signing in again; account restoration is not guaranteed.

The project does not provide a command that automatically uninstalls your app. Backups may contain session credentials: keep them private.
