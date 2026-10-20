package com.liskovsoft.smartyoutubetv2.common.misc;

import com.liskovsoft.youtubeapi.videoinfo.V2.VideoInfoService;

import com.liskovsoft.youtubeapi.common.helpers.AppClient;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import java.lang.reflect.Field;
import static org.junit.Assert.*;

/** Only constructs local services; it never makes a format or network request. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class PreparationStrategyTest {
    private VideoInfoService active;

    @Before public void setup() throws Exception {
        set(null, "sInstance", null);
        active = VideoInfoService.instance();
    }

    @Test public void preparationStartsWithTheChosenRecoveryClient() throws Exception {
        set(active, "mNextInfoType", AppClient.IOS);
        set(active, "mActualInfoType", AppClient.WEB);
        VideoInfoService prepared = VideoInfoService.createForPreparation();
        assertNotSame(active, prepared);
        assertEquals(AppClient.IOS, get(prepared, "mNextInfoType"));
        assertEquals(AppClient.IOS, get(prepared, "mPreparationStartType"));
        assertEquals(true, get(prepared, "mIsIsolated"));
        assertNull(get(prepared, "mActualInfoType"));
    }

    @Test public void preparationDoesNotMutateTheActiveClientOrPlaybackState() throws Exception {
        set(active, "mNextInfoType", AppClient.IOS);
        set(active, "mActualInfoType", AppClient.WEB);
        set(active, "mIsUnplayable", false);
        VideoInfoService prepared = VideoInfoService.createForPreparation();
        set(prepared, "mNextInfoType", AppClient.VISIONOS);
        set(prepared, "mActualInfoType", AppClient.VISIONOS);
        set(prepared, "mIsUnplayable", true);
        assertEquals(AppClient.IOS, get(active, "mNextInfoType"));
        assertEquals(AppClient.WEB, get(active, "mActualInfoType"));
        assertEquals(false, get(active, "mIsUnplayable"));
    }

    @Test public void activationKeepsAnOverrideChangedDuringPreparation() throws Exception {
        set(active, "mNextInfoType", AppClient.IOS);
        VideoInfoService prepared = VideoInfoService.createForPreparation();
        set(prepared, "mActualInfoType", AppClient.IOS);
        set(active, "mNextInfoType", AppClient.MWEB);
        active.activatePreparedState(prepared);
        assertEquals(AppClient.MWEB, get(active, "mNextInfoType"));
        assertEquals(AppClient.IOS, get(active, "mActualInfoType"));
    }

    @Test public void defaultPreparationCannotEraseALaterRecoveryOverride() throws Exception {
        VideoInfoService prepared = VideoInfoService.createForPreparation();
        assertNull(get(prepared, "mNextInfoType"));
        set(prepared, "mActualInfoType", AppClient.WEB_EMBED);
        set(active, "mNextInfoType", AppClient.VISIONOS);
        active.activatePreparedState(prepared);
        assertEquals(AppClient.VISIONOS, get(active, "mNextInfoType"));
    }

    @Test public void activationTransfersTheResolvedClientAndStatus() throws Exception {
        set(active, "mNextInfoType", AppClient.IOS);
        set(active, "mActualInfoType", AppClient.WEB);
        VideoInfoService prepared = VideoInfoService.createForPreparation();
        set(prepared, "mActualInfoType", AppClient.VISIONOS);
        set(prepared, "mIsUnplayable", false);
        active.activatePreparedState(prepared);
        assertEquals(AppClient.VISIONOS, get(active, "mActualInfoType"));
        assertEquals(AppClient.IOS, get(active, "mNextInfoType"));
        assertEquals(false, get(active, "mIsUnplayable"));
    }

    private static Object get(VideoInfoService service, String name) throws Exception {
        Field field = VideoInfoService.class.getDeclaredField(name);
        field.setAccessible(true);
        return field.get(service);
    }

    private static void set(VideoInfoService service, String name, Object value) throws Exception {
        Field field = VideoInfoService.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(service, value);
    }
}
