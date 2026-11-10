package com.liskovsoft.smartyoutubetv2.common.misc;

import com.liskovsoft.youtubeapi.app.PlaybackNonceState;
import com.liskovsoft.youtubeapi.app.AppService;
import com.liskovsoft.youtubeapi.common.helpers.AppClient;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import java.lang.reflect.Field;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.Test;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class PlaybackNonceIsolationTest {
    @Test public void concurrentPreparationDoesNotChangeCurrentHistoryUntilActivation() throws Exception {
        PlaybackNonceState state = new PlaybackNonceState();
        assertEquals("current", state.get(() -> "current"));
        String[] prepared = new String[1];
        Thread worker = new Thread(() -> {
            state.beginIsolated();
            try {
                state.reset();
                prepared[0] = state.get(() -> "next");
            } finally { state.endIsolated(); }
        });
        worker.start();
        worker.join();
        assertEquals("current", state.get(() -> "unexpected"));
        state.activate(prepared[0]);
        assertEquals("next", state.get(() -> "unexpected"));
    }

    @Test public void failedPreparationCleansUpThreadContext() {
        PlaybackNonceState state = new PlaybackNonceState();
        state.activate("current");
        state.beginIsolated();
        try { state.get(() -> "discarded"); }
        finally { state.endIsolated(); }
        state.reset();
        assertEquals("fresh", state.get(() -> "fresh"));
    }

    @Test public void pendingSpeculativeNonceDoesNotBlockCurrentPlaybackReads() throws Exception {
        PlaybackNonceState state = new PlaybackNonceState();
        state.activate("playing");
        CountDownLatch entered = new CountDownLatch(1);
        CountDownLatch finish = new CountDownLatch(1);
        Thread worker = new Thread(() -> {
            state.beginIsolated();
            try {
                state.get(() -> {
                    entered.countDown();
                    try {
                        if (!finish.await(5, TimeUnit.SECONDS)) throw new AssertionError("Preparation not released");
                    } catch (InterruptedException error) {
                        Thread.currentThread().interrupt();
                        throw new AssertionError(error);
                    }
                    return "prepared";
                });
            } finally { state.endIsolated(); }
        });
        worker.setDaemon(true);
        worker.start();
        try {
            assertTrue(entered.await(2, TimeUnit.SECONDS));
            FutureTask<String> read = new FutureTask<>(() -> state.get(() -> "unexpected"));
            Thread reader = new Thread(read);
            reader.setDaemon(true);
            reader.start();
            assertEquals("playing", read.get(1, TimeUnit.SECONDS));
        } finally {
            finish.countDown();
            worker.join(2_000);
        }
        assertEquals("playing", state.get(() -> "unexpected"));
    }

    @Test public void tvClientAndDefaultNonceOverloadsShareOnlyTheIsolatedContext() throws Exception {
        AppService app = AppService.instance();
        Field field = AppService.class.getDeclaredField("mPlaybackNonce");
        field.setAccessible(true);
        PlaybackNonceState state = (PlaybackNonceState) field.get(app);
        app.activatePreparedNonce("playing");
        app.beginShortsPreparation();
        try {
            assertEquals("prepared-tv", state.get(() -> "prepared-tv"));
            assertEquals("prepared-tv", app.getClientPlaybackNonce(AppClient.TV));
            assertEquals("prepared-tv", app.getClientPlaybackNonce());
            app.resetClientPlaybackNonce();
            assertEquals("prepared-retry", state.get(() -> "prepared-retry"));
            assertEquals("prepared-retry", app.getClientPlaybackNonce(AppClient.TV));
        } finally { app.endShortsPreparation(); }
        assertEquals("playing", app.getClientPlaybackNonce());
        assertEquals("playing", app.getClientPlaybackNonce(AppClient.TV));
    }
}
