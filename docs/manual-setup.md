# Shorts Slider — usage and settings

[Home](../README.md) · **English** · [Français](manual-setup.fr.md)

**This guide is for our SmartTube Shorts Slider APK.** It does not promise the same behavior in official SmartTube. The reported official-app trials did not reproduce the expected result; see [official settings and their limitations](official-settings.md).

## Enabled by default

On a **new profile**, Shorts Slider enables **up/down navigation**, **autoplay**, its **player button** and **next-Short preparation**. No configuration script is needed for our APK.

Existing installations and profiles retain saved choices, so their settings can differ from these defaults.

## Next and previous Short

Open a Short recognized by the app and wait for the player controls to disappear: **↓ Down** requests the next Short and **↑ Up** the previous one when available. When controls or a menu are visible, the arrows navigate that interface.

Change shortcuts under **Settings → General → Key remapping**.

| Choice | Setting |
| --- | --- |
| Up/down | **Skip Shorts with up/down buttons** — enabled on a new profile |
| Left/right | **Skip shorts with left/right buttons** — right = next, left = previous |
| Neither Shorts shortcut | Uncheck the currently enabled Shorts navigation option |

Up/down and left/right are mutually exclusive. Changing them can also reset custom assignments for those keys, including left/right volume control. Note existing choices before changing them.

Disabling these shortcuts does not disable autoplay.

## Autoplay or repeat

The **Auto-scroll Shorts** button before **Quality** is shown only for Shorts when its visibility option is enabled:

- **ON:** advance to an available next Short at the end.
- **OFF:** repeat the current Short.

It shares **Settings → Video player → Misc → Loop Shorts**: checking Loop Shorts means autoplay OFF. Our version does not require changing the global playback mode to control Shorts autoplay.

Autoplay stops when no next Short is available. The button does not create an infinite feed.

## Hide the button

Under **Settings → Video player → Setup player buttons**, uncheck **Show Shorts auto-scroll button**.

**Hiding the button does not disable autoplay.** Switch it OFF first, or enable **Loop Shorts** under **Misc**.

## Disable next-Short preparation

Under **Settings → Video player → Misc**, uncheck **Prepare the next Short**. It is enabled by default; navigation and the button still work when it is disabled.

Preparation fetches playback formats and stream addresses for **one next Short**. It does not download ten videos or prepare the first Short before you open it. Initial loading can still take time; speed improvements have not been measured.

## Profiles and playlists

If separate settings per account are enabled, check the relevant profile. Otherwise settings are shared.

**Use the content of the current section as a playlist**, under **Video player → Misc**, remains an optional native setting that also affects other videos. Our Shorts navigation does not require it to select available Shorts from Home.

Long portrait videos are not classified as Shorts solely because of their shape. See the [user guide](user-guide.md) for installation, account preservation and updates.
