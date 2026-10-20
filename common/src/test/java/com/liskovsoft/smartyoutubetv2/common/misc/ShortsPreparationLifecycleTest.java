package com.liskovsoft.smartyoutubetv2.common.misc;

import android.content.Context;
import com.liskovsoft.mediaserviceinterfaces.data.MediaItemFormatInfo;
import com.liskovsoft.sharedutils.prefs.GlobalPreferences;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.Playlist;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.Video;
import com.liskovsoft.smartyoutubetv2.common.app.models.playback.controllers.SuggestionsController;
import com.liskovsoft.smartyoutubetv2.common.app.models.playback.controllers.VideoLoaderController;
import com.liskovsoft.smartyoutubetv2.common.app.views.PlaybackView;
import com.liskovsoft.smartyoutubetv2.common.prefs.PlayerTweaksData;
import com.liskovsoft.youtubeapi.service.PreparedShort;
import io.reactivex.Observable;
import io.reactivex.subjects.PublishSubject;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

import java.lang.reflect.Field;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class ShortsPreparationLifecycleTest {
    private Context context;
    private Video current;
    private Video next;
    private boolean playing;
    private long duration;
    private VideoLoaderController controller;
    private PublishSubject<PreparedShort> pending;
    private AtomicInteger preparations;
    private AtomicInteger foreground;
    private AtomicInteger cancelledForeground;

    @Before public void setup() throws Exception {
        context = RuntimeEnvironment.getApplication();
        GlobalPreferences.instance(context);
        Playlist.instance().clear();
        PlayerTweaksData.instance(context).setShortsPreparationEnabled(true);
        current = video("current");
        next = video("next");
        pending = PublishSubject.create();
        preparations = new AtomicInteger();
        foreground = new AtomicInteger();
        cancelledForeground = new AtomicInteger();
        PlaybackView player = (PlaybackView) Proxy.newProxyInstance(PlaybackView.class.getClassLoader(),
                new Class<?>[]{PlaybackView.class}, (object, method, arguments) -> {
                    if (method.getName().equals("isPlaying")) return playing;
                    if (method.getName().equals("getDurationMs")) return duration;
                    Class<?> type = method.getReturnType();
                    if (!type.isPrimitive() || type == void.class) return null;
                    if (type == boolean.class) return false;
                    if (type == long.class) return 0L;
                    if (type == float.class) return 0f;
                    return 0;
                });
        controller = new VideoLoaderController() {
            @Override public PlaybackView getPlayer() { return player; }
            @Override public Video getVideo() { return current; }
            @Override public Context getContext() { return context; }
            @Override protected Observable<MediaItemFormatInfo> loadRegularFormatInfo(String id) {
                foreground.incrementAndGet();
                return Observable.<MediaItemFormatInfo>never().doOnDispose(cancelledForeground::incrementAndGet);
            }
        };
        SuggestionsController suggestions = new SuggestionsController() {
            @Override public Video getNext() { return next; }
        };
        set("mSuggestionsController", suggestions);
        set("mNextVideoPreloader", new NextVideoPreloader<>(id -> {
            preparations.incrementAndGet();
            return pending;
        }, () -> 0, value -> true));
    }

    @Test public void readyEventStartsPreparationWhenSourceAndMetadataPrecedePlayback() {
        controller.onVideoLoaded(current);
        controller.onMetadata(null);
        assertEquals(0, preparations.get());
        playing = true;
        duration = 10_000;
        controller.onPlay();
        assertEquals(1, preparations.get());
        assertTrue(pending.hasObservers());
        controller.onPlay();
        controller.onMetadata(null);
        assertEquals(1, preparations.get());
    }

    @Test public void metadataArrivingAfterReadyStartsPreparationImmediately() {
        playing = true;
        duration = 10_000;
        Video available = next;
        next = null;
        controller.onPlay();
        assertEquals(0, preparations.get());
        next = available;
        controller.onMetadata(null);
        assertEquals(1, preparations.get());
    }

    @Test public void foregroundJoinsPendingPreparationAndFallsBackOnlyOnceAfterError() throws Exception {
        playing = true;
        duration = 10_000;
        controller.onPlay();
        current = next;
        loadFormats();
        assertEquals(1, preparations.get());
        assertEquals(0, foreground.get());
        assertTrue(pending.hasObservers());
        pending.onError(new IllegalStateException("synthetic preparation failure"));
        assertEquals(1, preparations.get());
        assertEquals(1, foreground.get());
        controller.onEngineReleased();
        assertEquals(1, cancelledForeground.get());
    }

    @Test public void preparationRejectedAtActivationUsesExactlyOneForegroundFallback() throws Exception {
        playing = true;
        duration = 10_000;
        controller.onPlay();
        current = next;
        loadFormats();
        assertEquals(0, foreground.get());
        Constructor<?> constructor = PreparedShort.class.getDeclaredConstructors()[0];
        constructor.setAccessible(true);
        PreparedShort expired = (PreparedShort) constructor.newInstance(null, null, null, null);
        pending.onNext(expired); // Real activate() rejects this result at its final validity check.
        assertEquals(1, preparations.get());
        assertEquals(1, foreground.get());
        controller.onFinish();
        assertEquals(1, cancelledForeground.get());
    }

    @Test public void stalePreparationFailureCannotStartLookupForTheReplacementVideo() throws Exception {
        playing = true;
        duration = 10_000;
        controller.onPlay();
        current = next;
        loadFormats();
        current = video("replacement");
        pending.onError(new IllegalStateException("late preparation failure"));
        assertEquals(0, foreground.get());
        controller.onFinish();
    }

    @Test public void leavingDuringPendingForegroundPreparationCancelsItWithoutFallback() throws Exception {
        playing = true;
        duration = 10_000;
        controller.onPlay();
        current = next;
        loadFormats();
        assertTrue(pending.hasObservers());
        controller.onFinish();
        assertFalse(pending.hasObservers());
        pending.onError(new IllegalStateException("late failure"));
        assertEquals(0, foreground.get());
    }

    @Test public void openingAnotherVideoCancelsTheUnrelatedPreparedRequest() throws Exception {
        playing = true;
        duration = 10_000;
        controller.onPlay();
        current = video("different");
        loadFormats();
        assertFalse(pending.hasObservers());
        assertEquals(1, preparations.get());
        assertEquals(1, foreground.get());
        controller.onFinish();
    }

    private Video video(String id) {
        Video video = new Video();
        video.videoId = id;
        video.isShorts = true;
        return video;
    }

    private void set(String name, Object value) throws Exception {
        Field field = VideoLoaderController.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(controller, value);
    }

    private void loadFormats() throws Exception {
        Method method = VideoLoaderController.class.getDeclaredMethod("loadFormatInfo", Video.class);
        method.setAccessible(true);
        method.invoke(controller, current);
    }
}
