package com.liskovsoft.smartyoutubetv2.common.misc;

import com.liskovsoft.youtubeapi.videoinfo.V2.VideoInfoService;
import com.liskovsoft.youtubeapi.service.internal.FormatInfoWrapper;
import com.liskovsoft.mediaserviceinterfaces.data.MediaItemFormatInfo;

import com.liskovsoft.youtubeapi.common.helpers.AppClient;
import com.liskovsoft.youtubeapi.app.ReloadPlaybackGate;
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
        assertEquals(Arrays.asList("auth", "legacy", "legacy", "innertube"), preparation.calls);
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

    @Test public void preparationUsesTheCurrentClientOverrideWithoutChangingIt() throws Exception {
        Object active = activeContext();
        Object old = contextField(active, "mNextClient");
        try {
            Object web = clientEntry(AppClient.WEB);
            contextField(active, "mNextClient", web);
            FormatInfoWrapper.LookupContext preparation = FormatInfoWrapper.createForPreparation(
                    VideoInfoService.createForPreparation());
            assertEquals(AppClient.WEB, preparation.getActualClient());
            preparation.switchNextClient(true);
            assertNotEquals(AppClient.WEB, preparation.getActualClient());
            assertSame(web, contextField(active, "mNextClient"));
        } finally {
            contextField(active, "mNextClient", old);
        }
    }

    @Test public void activationKeepsARecoveryChoiceMadeDuringPreparation() throws Exception {
        Object active = activeContext();
        Object oldClient = contextField(active, "mNextClient");
        Object oldActual = contextField(active, "mActualClient");
        Object oldGeneration = contextField(active, "strategyGeneration");
        Object oldCache = contextField(active, "mCachedFormatInfo");
        try {
            Object web = clientEntry(AppClient.WEB);
            Object ios = clientEntry(AppClient.IOS);
            contextField(active, "mNextClient", ios);
            FormatInfoWrapper.LookupContext preparation = FormatInfoWrapper.createForPreparation(
                    VideoInfoService.createForPreparation());
            contextField(preparation, "mActualClient", ios);
            contextField(active, "mActualClient", web);
            FormatInfoWrapper.switchNextClient(true);
            AppClient recovery = FormatInfoWrapper.getActualClient();
            MediaItemFormatInfo next = format("next", false);
            FormatInfoWrapper.activatePreparedFormat(next, preparation);
            assertSame(next, contextField(active, "mCachedFormatInfo"));
            assertSame(web, contextField(active, "mActualClient"));
            assertEquals(recovery, FormatInfoWrapper.getActualClient());
            assertNotEquals(AppClient.IOS, recovery);
        } finally {
            contextField(active, "mNextClient", oldClient);
            contextField(active, "mActualClient", oldActual);
            contextField(active, "strategyGeneration", oldGeneration);
            contextField(active, "mCachedFormatInfo", oldCache);
        }
    }

    private static Object clientEntry(AppClient client) throws Exception {
        Field field = FormatInfoWrapper.class.getDeclaredField("CLIENT_LIST");
        field.setAccessible(true);
        for (Object entry : (Object[]) field.get(null)) {
            if (((kotlin.Pair<?, ?>) entry).getFirst() == client) return entry;
        }
        throw new AssertionError("Client not configured: " + client);
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
            @Override protected MediaItemFormatInfo requestLegacyFormatInfo(AppClient client, String id, String tracking) {
                entered.countDown();
                try {
                    if (!release.await(5, TimeUnit.SECONDS)) throw new AssertionError("Release was not signalled");
                } catch (InterruptedException error) { throw new AssertionError(error); }
                return super.requestLegacyFormatInfo(client, id, tracking);
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
        @Override protected MediaItemFormatInfo requestLegacyFormatInfo(AppClient client, String id, String tracking) {
            calls.add("legacy");
            return legacy;
        }
        @Override protected MediaItemFormatInfo requestInnertubeFormatInfo(AppClient client, String id) {
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
}
