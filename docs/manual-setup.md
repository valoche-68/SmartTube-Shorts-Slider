# Configure Shorts with your remote

[Home](../README.md) · **English** · [Français](manual-setup.fr.md)

This tutorial enables the same navigation and playback options as our script, directly in **official SmartTube**. Everything is done on your TV, with no computer or ADB needed.

The menus below were checked against official **32.56 stable and beta** source code. Labels may differ in other versions; Fire TV testing remains pending. Note your current settings so you can restore them later.

If you use multiple accounts, first select the one to configure under **Settings → Accounts**. With **Use separate settings per each account** enabled, repeat the settings for each account you want to configure; otherwise, settings are shared.

## 1. Move between Shorts with up/down

1. From the home screen, open **Settings → General → Key remapping**.
2. Enable **Skip Shorts with up/down buttons**.
3. Open a Short from a Shorts section and wait for the player controls to disappear.

Selecting up/down automatically disables Shorts left/right navigation. Simply enable the option you want.

**↓ Down** plays the next video; **↑ Up** returns to the previous one when available. While controls or a menu are visible, the arrows navigate that interface.

Choose the option mentioning **Shorts**: the one for regular videos is a separate setting. Changing the Shorts up/down option also resets its associated key remapping, so a custom action on those keys may be replaced.

## 2. Automatically play the next video when a Short ends

1. Open **Settings → Player → Misc** and **disable “Loop Shorts”**.
2. Return to **Player → Playback mode** and select **Play videos continuously**.

The second setting is a separate category under **Player**, outside **Misc**. It also applies to regular videos, allowing them to play continuously too.

Arrow navigation and automatic playback are independent. You can keep up/down navigation while setting Shorts to loop again.

## 3. Use the current section as the playlist

In **Settings → Player → Misc**, enable **Use current section contents as a playlist**. Return to the Shorts section and open a video from that list.

This optional setting uses the section’s videos as the playback list. It also affects other sections. A list containing regular videos does not become a Shorts-only playlist.

## Choose other options or restore your settings

| You want to… | Setting to change |
| --- | --- |
| Use left/right | In **Key remapping**, enable **Skip Shorts with left/right buttons**. Up/down is disabled automatically. Right = next; left = previous. |
| Disable Shorts shortcuts | Uncheck the currently enabled Shorts navigation option in that menu. |
| Repeat the current Short | Enable **Player → Misc → Loop Shorts** again. |
| Stop using the section as a playlist | Disable **Use current section contents as a playlist**. |
| Restore regular videos’ previous behavior | Restore your original choice under **Player → Playback mode**. |

Changing left/right navigation also resets its volume remapping. To fully undo your changes, restore the values you noted beforehand, including custom key actions. Enabling Loop Shorts again does not by itself restore the previous global playback mode.

To **inspect** your configuration, return to these menus: the checked options and selected playback mode show your current settings.

## Check the result

Open a Short from a Shorts section containing several videos. Test down and up with the controls hidden, then let a Short finish to check automatic playback. Close and reopen SmartTube and verify your choices in the same profile.

If it does not work, check your profile, both autoplay settings and where you opened the video: native navigation depends in particular on its membership in a Shorts group. A portrait video opened elsewhere may not be recognized in the same way. What plays next depends on the available videos; these settings do not guarantee an endless or exclusively Shorts sequence in every context.

This keeps the official app. It **does not add Shorts Slider’s autoplay button or our next-Short preparation**.

---

References: official [key remapping](https://github.com/yuliskov/SmartTube/blob/32.56s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/presenters/settings/GeneralSettingsPresenter.java), [player settings](https://github.com/yuliskov/SmartTube/blob/32.56s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/presenters/settings/PlayerSettingsPresenter.java) and [English labels](https://github.com/yuliskov/SmartTube/blob/32.56s/common/src/main/res/values/strings.xml).
