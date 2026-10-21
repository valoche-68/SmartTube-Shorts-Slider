package com.liskovsoft.smartyoutubetv2.common.misc;

import com.liskovsoft.youtubeapi.videoinfo.V2.VideoInfoService;
import com.liskovsoft.youtubeapi.service.internal.FormatInfoWrapper;
import com.liskovsoft.mediaserviceinterfaces.data.MediaItemFormatInfo;

import com.liskovsoft.youtubeapi.common.helpers.AppClient;
import com.liskovsoft.youtubeapi.app.ReloadPlaybackGate;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
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

    @Test public void privateWrapperCacheNeverChangesTheActiveCache() throws Exception {
        Object activeContext = activeContext();
        MediaItemFormatInfo playing = format("playing", false);
        Object old = contextField(activeContext, "mCachedFormatInfo");
        contextField(activeContext, "mCachedFormatInfo", playing);
        try {
            FormatInfoWrapper.LookupContext preparation = FormatInfoWrapper.createForPreparation(
                    VideoInfoService.createForPreparation());
            assertNull(contextField(preparation, "mCachedFormatInfo"));
            FakeContext isolated = new FakeContext(format("next", false), null);
            assertEquals("next", isolated.getFormatInfo("next", null).getVideoId());
            assertSame(playing, contextField(activeContext, "mCachedFormatInfo"));
            assertSame(playing, FormatInfoWrapper.getFormatInfo("playing", null));
        } finally {
            contextField(activeContext, "mCachedFormatInfo", old);
        }
    }

    @Test public void normalLookupAuthenticatesAndReusesTheOneVideoCache() {
        FakeContext preparation = new FakeContext(format("next", false), null);
        MediaItemFormatInfo first = preparation.getFormatInfo("next", null);
        assertSame(first, preparation.getFormatInfo("next", null));
        assertEquals(Arrays.asList("auth", "legacy"), preparation.calls);
        preparation.getFormatInfo("different", null);
        assertEquals(Arrays.asList("auth", "legacy", "auth", "legacy"), preparation.calls);
    }

    @Test public void normalLookupRetainsAuthenticationAndInnertubeFallback() {
        MediaItemFormatInfo fallback = format("next", false);
        FakeContext preparation = new FakeContext(format("next", true), fallback);
        assertSame(fallback, preparation.getFormatInfo("next", null));
        assertEquals(Arrays.asList("auth", "legacy", "auth", "innertube"), preparation.calls);
        assertSame(fallback, preparation.getFormatInfo("next", null));
        assertEquals(4, preparation.calls.size());
    }

    @Test public void finishingPreparationDoesNotClearForegroundRecoveryForTheSameVideo() {
        ReloadPlaybackGate.setToken("next", "foreground-recovery");
        try {
            FakeContext preparation = new FakeContext(format("next", false), null);
            preparation.getFormatInfo("next", null);
            assertEquals("foreground-recovery", ReloadPlaybackGate.getToken("next"));
        } finally { ReloadPlaybackGate.reset("next"); }
    }

    @Test public void preparationCopiesTheCurrentInnertubeFirstStrategyWithoutSharingIt() throws Exception {
        Object activeContext = activeContext();
        Object old = contextField(activeContext, "mTryInnertubeFirst");
        contextField(activeContext, "mTryInnertubeFirst", true);
        try {
            FormatInfoWrapper.LookupContext preparation = FormatInfoWrapper.createForPreparation(
                    VideoInfoService.createForPreparation());
            assertEquals(true, contextField(preparation, "mTryInnertubeFirst"));
            contextField(preparation, "mTryInnertubeFirst", false);
            assertEquals(true, contextField(activeContext, "mTryInnertubeFirst"));
        } finally {
            contextField(activeContext, "mTryInnertubeFirst", old);
        }
    }

    @Test public void activationPreservesANewerWrapperRecoveryChoice() throws Exception {
        Object activeContext = activeContext();
        Object oldStrategy = contextField(activeContext, "mTryInnertubeFirst");
        Object oldGeneration = contextField(activeContext, "mStrategyGeneration");
        Object oldCache = contextField(activeContext, "mCachedFormatInfo");
        contextField(activeContext, "mStrategyGeneration", 40L);
        contextField(activeContext, "mTryInnertubeFirst", false);
        try {
            FormatInfoWrapper.LookupContext preparation = FormatInfoWrapper.createForPreparation(
                    VideoInfoService.createForPreparation());
            contextField(activeContext, "mStrategyGeneration", 41L);
            contextField(activeContext, "mTryInnertubeFirst", true);
            MediaItemFormatInfo next = format("next", false);
            FormatInfoWrapper.activatePreparedFormat(next, preparation);
            assertSame(next, contextField(activeContext, "mCachedFormatInfo"));
            assertEquals(true, contextField(activeContext, "mTryInnertubeFirst"));
        } finally {
            contextField(activeContext, "mCachedFormatInfo", oldCache);
            contextField(activeContext, "mTryInnertubeFirst", oldStrategy);
            contextField(activeContext, "mStrategyGeneration", oldGeneration);
        }
    }

    @Test public void aBlockedPreparationDoesNotHoldTheActiveLookupLock() throws Exception {
        Object activeContext = activeContext();
        Object old = contextField(activeContext, "mCachedFormatInfo");
        MediaItemFormatInfo playing = format("playing", false);
        contextField(activeContext, "mCachedFormatInfo", playing);
        CountDownLatch entered = new CountDownLatch(1);
        CountDownLatch release = new CountDownLatch(1);
        CountDownLatch finished = new CountDownLatch(1);
        AtomicReference<Throwable> failure = new AtomicReference<>();
        FakeContext isolated = new FakeContext(format("next", false), null) {
            @Override protected MediaItemFormatInfo requestLegacyFormatInfo(String id, String tracking) {
                entered.countDown();
                try {
                    if (!release.await(5, TimeUnit.SECONDS)) throw new AssertionError("Release was not signalled");
                } catch (InterruptedException error) { throw new AssertionError(error); }
                return super.requestLegacyFormatInfo(id, tracking);
            }
        };
        Thread prepare = new Thread(() -> isolated.getFormatInfo("next", null));
        Thread foreground = new Thread(() -> {
            try { assertSame(playing, FormatInfoWrapper.getFormatInfo("playing", null)); }
            catch (Throwable error) { failure.set(error); }
            finally { finished.countDown(); }
        });
        try {
            prepare.start();
            assertTrue(entered.await(3, TimeUnit.SECONDS));
            foreground.start();
            assertTrue("Foreground lookup waited for speculative work", finished.await(3, TimeUnit.SECONDS));
            assertNull(failure.get());
        } finally {
            release.countDown();
            prepare.join(5000);
            foreground.join(5000);
            contextField(activeContext, "mCachedFormatInfo", old);
        }
    }

    private static class FakeContext extends FormatInfoWrapper.LookupContext {
        final List<String> calls = new ArrayList<>();
        private final MediaItemFormatInfo legacy;
        private final MediaItemFormatInfo fallback;

        FakeContext(MediaItemFormatInfo legacy, MediaItemFormatInfo fallback) {
            super(null, true);
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

    private static Object activeContext() throws Exception {
        Field field = FormatInfoWrapper.class.getDeclaredField("active");
        field.setAccessible(true);
        return field.get(null);
    }

    private static Object contextField(Object target, String name) throws Exception {
        Field field = FormatInfoWrapper.LookupContext.class.getDeclaredField(name);
        field.setAccessible(true);
        return field.get(target);
    }

    private static void contextField(Object target, String name, Object value) throws Exception {
        Field field = FormatInfoWrapper.LookupContext.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(target, value);
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
