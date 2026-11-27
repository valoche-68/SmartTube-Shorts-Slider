# Official SmartTube — settings and script limitations

[Home](../README.md) · **English** · [Français](official-settings.fr.md)

**Configuring official SmartTube is not a validated alternative to Shorts Slider for our use case.** Enabling its settings did not reproduce the expected navigation and autoplay behavior in the reported Fire TV trials. This does not prove these functions cannot work on other devices or versions.

## What was checked in source code

Official **32.56 and 32.68** contain preferences for Shorts navigation, looping and section playlists. The existence of those preferences does not establish working playback behavior.

In base **32.68**, the player’s Shorts shortcuts depend in particular on the video belonging to a **Shorts group**. Setting a preference does not change recognition or next-video selection. A Short opened from Home can therefore follow a different path from one opened in a dedicated section.

The script only edits values in an official backup. It does not fix that playback path, add the button or reproduce our preparation handling. Synthetic-backup tests check value changes and selective undo, not TV playback.

## What our version changes

Shorts Slider reuses native preferences but also modifies Shorts recognition, identity retention and next-Short selection. It adds the ON/OFF button and optional preparation in a separate context.

Up/down and autoplay are already enabled for new profiles in our APK. Its [settings guide](manual-setup.md) explains how to disable them, hide the button or disable preparation. **The official-app script is not for configuring our APK**; it rejects custom builds.

## Official assistant status

The script remains an **experimental backup-editing tool**, rather than a recommended way to obtain Shorts Slider behavior. Its full TV restoration workflow has not been validated. The reviewed preference formats are 32.56 and 32.68; unknown versions are rejected.

Commands remain in the [assistant’s technical documentation](configuration-native.md) for deliberate backup-based experiments. Changing the global playback mode can also enable autoplay for long videos. No TV restore is needed to use Shorts Slider’s own settings.

Reviewed upstream sources: [player shortcuts](https://github.com/yuliskov/SmartTube/blob/32.68s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/playback/controllers/PlayerUIController.java), [next-video selection](https://github.com/yuliskov/SmartTube/blob/32.68s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/playback/controllers/SuggestionsController.java), [preferences](https://github.com/yuliskov/SmartTube/blob/32.68s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/prefs/PlayerTweaksData.java).
