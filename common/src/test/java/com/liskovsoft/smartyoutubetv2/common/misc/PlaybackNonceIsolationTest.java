package com.liskovsoft.smartyoutubetv2.common.misc;

import com.liskovsoft.youtubeapi.app.PlaybackNonceState;
import org.junit.Test;
import static org.junit.Assert.*;

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
}
