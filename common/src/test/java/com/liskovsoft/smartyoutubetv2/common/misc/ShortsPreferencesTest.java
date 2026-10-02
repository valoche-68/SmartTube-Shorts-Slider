package com.liskovsoft.smartyoutubetv2.common.misc;

import android.content.Context;
import android.os.Looper;
import com.liskovsoft.sharedutils.helpers.Helpers;
import com.liskovsoft.smartyoutubetv2.common.prefs.AppPrefs;
import com.liskovsoft.smartyoutubetv2.common.prefs.PlayerTweaksData;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import java.lang.reflect.Field;
import java.util.Arrays;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class ShortsPreferencesTest {
    private Context context;
    private AppPrefs prefs;
    private PlayerTweaksData tweaks;

    @Before public void setup() throws Exception {
        context = RuntimeEnvironment.getApplication();
        for (Class<?> type : new Class<?>[]{AppPrefs.class, PlayerTweaksData.class}) {
            Field instance = type.getDeclaredField("sInstance");
            instance.setAccessible(true);
            instance.set(null, null);
        }
        prefs = AppPrefs.instance(context);
        prefs.setProfileData("video_player_tweaks_data", null);
        prefs.setProfileData("shorts_slider_button_visible", null);
        prefs.setProfileData("shorts_slider_preparation_enabled", null);
        prefs.setProfileData("shorts_slider_migrated", null);
        tweaks = PlayerTweaksData.instance(context);
    }

    @Test public void newProfileDefaultsAndIndependentVisibilityPersist() {
        assertTrue(tweaks.isQuickSkipShortsAltEnabled());
        assertFalse(tweaks.isQuickSkipShortsEnabled());
        assertTrue(tweaks.isShortsAutoScrollEnabled());
        assertTrue(tweaks.isShortsPreparationEnabled());
        tweaks.setShortsButtonVisible(false);
        tweaks.setShortsPreparationEnabled(false);
        tweaks.onProfileChanged();
        assertFalse(tweaks.isShortsButtonVisible());
        assertFalse(tweaks.isShortsPreparationEnabled());
        assertTrue(tweaks.isShortsAutoScrollEnabled());
    }

    @Test public void legacyToggleMigratesOnceAndNativeLoopControlsButton() {
        String[] data = new String[62];
        Arrays.fill(data, "null");
        data[44] = "false";
        data[57] = "false";
        data[61] = "false";
        prefs.setProfileData("video_player_tweaks_data", Helpers.mergeData((Object[]) data));
        tweaks.onProfileChanged();
        shadowOf(Looper.getMainLooper()).idle();
        assertTrue(tweaks.isLoopShortsEnabled());
        assertFalse(tweaks.isShortsAutoScrollEnabled());
        assertFalse(tweaks.isQuickSkipShortsAltEnabled());
        tweaks.setShortsAutoScrollEnabled(true);
        shadowOf(Looper.getMainLooper()).idle();
        tweaks.onProfileChanged();
        assertFalse(tweaks.isLoopShortsEnabled());
        tweaks.setLoopShortsEnabled(true);
        assertFalse(tweaks.isShortsAutoScrollEnabled());
    }
    @Test public void optionsAreScopedToTheSelectedProfile() {
        prefs.enableMultiProfiles(true);
        context.getSharedPreferences(context.getPackageName() + "_preferences", 0).edit()
                .putString("last_profile_name", "profile_a").commit();
        tweaks.onProfileChanged();
        tweaks.setShortsButtonVisible(false);
        tweaks.setShortsPreparationEnabled(false);
        context.getSharedPreferences(context.getPackageName() + "_preferences", 0).edit()
                .putString("last_profile_name", "profile_b").commit();
        tweaks.onProfileChanged();
        assertTrue(tweaks.isShortsButtonVisible());
        assertTrue(tweaks.isShortsPreparationEnabled());
        context.getSharedPreferences(context.getPackageName() + "_preferences", 0).edit()
                .putString("last_profile_name", "profile_a").commit();
        tweaks.onProfileChanged();
        assertFalse(tweaks.isShortsButtonVisible());
        assertFalse(tweaks.isShortsPreparationEnabled());
    }
}
