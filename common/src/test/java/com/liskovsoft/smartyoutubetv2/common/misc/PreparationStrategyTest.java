package com.liskovsoft.smartyoutubetv2.common.misc;

import com.liskovsoft.youtubeapi.videoinfo.V2.VideoInfoService;
import com.liskovsoft.youtubeapi.service.YouTubeMediaItemService;
import com.liskovsoft.mediaserviceinterfaces.data.MediaItemFormatInfo;

import com.liskovsoft.youtubeapi.common.helpers.AppClient;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import static org.junit.Assert.*;

/** Uses local services and fake format replies, without network or authentication requests. */
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

    @Test public void privateMediaServiceRetainsNormalCacheWithoutTouchingTheActiveCache() throws Exception {
        YouTubeMediaItemService playback = YouTubeMediaItemService.instance();
        MediaItemFormatInfo playing = format("playing", false);
        Field cache = YouTubeMediaItemService.class.getDeclaredField("mCachedFormatInfo");
        cache.setAccessible(true);
        Object old = cache.get(playback);
        cache.set(playback, playing);
        try {
            VideoInfoService isolated = VideoInfoService.createForPreparation();
            Method factory = YouTubeMediaItemService.class.getDeclaredMethod("createForPreparation", VideoInfoService.class);
            factory.setAccessible(true);
            YouTubeMediaItemService preparation = (YouTubeMediaItemService) factory.invoke(null, isolated);
            assertNotSame(playback, preparation);
            assertNull(cache.get(preparation));
            Field strategy = YouTubeMediaItemService.class.getDeclaredField("mPreparationVideoInfoService");
            strategy.setAccessible(true);
            assertSame(isolated, strategy.get(preparation));
            preparation.activatePreparedFormat(format("next", false)); // This instance's private cache only.
            assertEquals("next", ((MediaItemFormatInfo) cache.get(preparation)).getVideoId());
            assertSame(playing, cache.get(playback));
            assertSame(playback, YouTubeMediaItemService.instance());
        } finally {
            cache.set(playback, old);
        }
    }

    @Test public void normalLookupAuthenticatesAndReusesTheOneVideoCache() {
        FakeMediaService preparation = new FakeMediaService(format("next", false), null);
        MediaItemFormatInfo first = preparation.getFormatInfo("next");
        assertSame(first, preparation.getFormatInfo("next"));
        assertEquals(Arrays.asList("auth", "legacy"), preparation.calls);
        preparation.getFormatInfo("different");
        assertEquals(Arrays.asList("auth", "legacy", "auth", "legacy"), preparation.calls);
    }

    @Test public void normalLookupRetainsAuthenticationAndInnertubeFallback() {
        MediaItemFormatInfo fallback = format("next", false);
        FakeMediaService preparation = new FakeMediaService(format("next", true), fallback);
        assertSame(fallback, preparation.getFormatInfo("next"));
        assertEquals(Arrays.asList("auth", "legacy", "auth", "innertube"), preparation.calls);
        assertSame(fallback, preparation.getFormatInfo("next"));
        assertEquals(4, preparation.calls.size());
    }

    private static class FakeMediaService extends YouTubeMediaItemService {
        final List<String> calls = new ArrayList<>();
        private final MediaItemFormatInfo legacy;
        private final MediaItemFormatInfo fallback;

        FakeMediaService(MediaItemFormatInfo legacy, MediaItemFormatInfo fallback) {
            super(null);
            this.legacy = legacy;
            this.fallback = fallback;
        }

        @Override protected void checkSigned() { calls.add("auth"); }
        @Override protected MediaItemFormatInfo requestLegacyFormatInfo(String id, String tracking) {
            calls.add("legacy");
            return legacy;
        }
        @Override protected MediaItemFormatInfo requestInnertubeFormatInfo(String id) {
            calls.add("innertube");
            return fallback;
        }
    }

    private static MediaItemFormatInfo format(String id, boolean unplayable) {
        return (MediaItemFormatInfo) Proxy.newProxyInstance(MediaItemFormatInfo.class.getClassLoader(),
                new Class<?>[]{MediaItemFormatInfo.class}, (proxy, method, args) -> {
                    if (method.getName().equals("getVideoId")) return id;
                    if (method.getName().equals("isUnplayable")) return unplayable;
                    if (method.getName().equals("isCacheActual")) return !unplayable;
                    Class<?> type = method.getReturnType();
                    if (type == boolean.class) return false;
                    if (type == int.class) return 0;
                    if (type == long.class) return 0L;
                    if (type == float.class) return 0f;
                    return null;
                });
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
