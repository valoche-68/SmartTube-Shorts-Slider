package com.liskovsoft.smartyoutubetv2.common.misc;

import android.content.Context;
import android.os.Looper;
import com.liskovsoft.mediaserviceinterfaces.data.MediaItemFormatInfo;
import com.liskovsoft.sharedutils.prefs.GlobalPreferences;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.Playlist;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.Video;
import com.liskovsoft.smartyoutubetv2.common.app.models.playback.controllers.SuggestionsController;
import com.liskovsoft.smartyoutubetv2.common.app.models.playback.controllers.VideoLoaderController;
import com.liskovsoft.smartyoutubetv2.common.app.models.playback.listener.PlayerEventListener;
import com.liskovsoft.smartyoutubetv2.common.app.presenters.PlaybackPresenter;
import com.liskovsoft.smartyoutubetv2.common.app.views.PlaybackView;
import com.liskovsoft.smartyoutubetv2.common.prefs.PlayerTweaksData;
import com.liskovsoft.youtubeapi.service.PreparedShort;
import com.liskovsoft.youtubeapi.service.YouTubeSignInService;
import com.liskovsoft.youtubeapi.app.AppService;
import com.liskovsoft.youtubeapi.videoinfo.V2.VideoInfoService;
import io.reactivex.Observable;
import io.reactivex.subjects.PublishSubject;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;

import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
@LooperMode(LooperMode.Mode.PAUSED)
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
        PlaybackView player = proxy(PlaybackView.class, (name, args) -> {
            if (name.equals("isPlaying")) return playing;
            if (name.equals("getDurationMs")) return duration;
            return null;
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
        set(controller, "mSuggestionsController", suggestions);
        set(controller, "mNextVideoPreloader", new NextVideoPreloader<>(id -> {
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

    @Test public void foregroundStartsImmediatelyWhilePreparationIsStillPending() throws Exception {
        startPreparation();
        current = next;
        loadFormats(controller, current);
        assertEquals(1, preparations.get());
        assertEquals(1, foreground.get());
        assertFalse(pending.hasObservers());
        pending.onError(new IllegalStateException("late preparation failure"));
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(1, foreground.get());
        controller.onEngineReleased();
        assertEquals(1, cancelledForeground.get());
    }

    @Test public void readyPreparationRejectedAtActivationUsesExactlyOneForegroundFallback() throws Exception {
        startPreparation();
        Constructor<?> constructor = PreparedShort.class.getDeclaredConstructors()[0];
        constructor.setAccessible(true);
        pending.onNext((PreparedShort) constructor.newInstance(null, null, null, null));
        current = next;
        loadFormats(controller, current);
        assertEquals(0, foreground.get()); // Cached activation is posted after presenter dispatch.
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(1, preparations.get());
        assertEquals(1, foreground.get());
        controller.onFinish();
        assertEquals(1, cancelledForeground.get());
    }

    @Test public void leavingBeforeDeferredActivationCancelsItWithoutStartingFallback() throws Exception {
        startPreparation();
        Constructor<?> constructor = PreparedShort.class.getDeclaredConstructors()[0];
        constructor.setAccessible(true);
        pending.onNext((PreparedShort) constructor.newInstance(null, null, null, null));
        current = next;
        loadFormats(controller, current);
        controller.onFinish();
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(0, foreground.get());
    }

    @Test public void openingAnotherVideoCancelsTheUnrelatedPreparedRequest() throws Exception {
        startPreparation();
        current = video("different");
        loadFormats(controller, current);
        assertFalse(pending.hasObservers());
        assertEquals(1, preparations.get());
        assertEquals(1, foreground.get());
        controller.onFinish();
    }

    @Test public void rapidForegroundChangesCancelTheEarlierRequest() throws Exception {
        loadFormats(controller, current);
        assertEquals(1, foreground.get());
        current = video("different");
        loadFormats(controller, current);
        assertEquals(2, foreground.get());
        assertEquals(1, cancelledForeground.get());
        controller.onFinish();
        assertEquals(2, cancelledForeground.get());
    }

    @Test public void realPresenterDispatchStartsLookupBeforeVideoAssignmentAndAutoplayAfterCompletion() throws Exception {
        PresenterFixture fixture = new PresenterFixture();
        Video first = video("first");
        Video second = video("second");
        fixture.next = second;
        fixture.presenter.onNewVideo(first); // The presenter still exposes its OLD video inside this dispatch.
        assertEquals(Collections.singletonList("first"), fixture.lookups);
        assertEquals(Collections.singletonList("old"), fixture.presenterVideoDuringLookup);
        assertSame(first, fixture.presenter.getVideo());
        assertTrue(fixture.played.isEmpty()); // A synchronous cache result must wait for dispatch to finish.
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(Collections.singletonList("first"), fixture.played);
        assertTrue(fixture.formatSubscription().isDisposed());
        PlayerTweaksData.instance(context).setShortsAutoScrollEnabled(true);
        fixture.presenter.onPlayEnd();
        assertSame(second, fixture.presenter.getVideo());
        assertEquals(2, fixture.lookups.size());
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(2, fixture.played.size());
        fixture.presenter.onFinish();
    }

    @Test public void realPresenterAutoOffLoopsAfterFormatsCompleteWithoutOpeningTheNextVideo() throws Exception {
        PresenterFixture fixture = new PresenterFixture();
        Video first = video("first");
        fixture.next = video("second");
        fixture.presenter.onNewVideo(first);
        shadowOf(Looper.getMainLooper()).idle();
        assertTrue(fixture.formatSubscription().isDisposed());
        PlayerTweaksData.instance(context).setShortsAutoScrollEnabled(false);
        fixture.presenter.onPlayEnd();
        assertSame(first, fixture.presenter.getVideo());
        assertEquals(Collections.singletonList("first"), fixture.lookups);
        assertEquals(Collections.singletonList(0L), fixture.seeks);
        fixture.presenter.onFinish();
    }

    @Test public void realPresenterReadyCacheActivatesOnlyAfterDispatchAndNeedsNoNormalLookup() throws Exception {
        PresenterFixture fixture = new PresenterFixture();
        Constructor<?> constructor = PreparedShort.class.getDeclaredConstructors()[0];
        constructor.setAccessible(true);
        PreparedShort prepared = (PreparedShort) constructor.newInstance(format("first"),
                VideoInfoService.createForPreparation(), "prepared-nonce",
                YouTubeSignInService.instance().getSelectedAccount());
        NextVideoPreloader<PreparedShort> preloader = new NextVideoPreloader<>(
                id -> Observable.just(prepared), () -> 0, PreparedShort::isValid);
        preloader.prefetch("first");
        set(fixture.loader, "mNextVideoPreloader", preloader);
        AppService.instance().activatePreparedNonce("before-dispatch");
        Video first = video("first");
        fixture.presenter.onNewVideo(first);
        assertSame(first, fixture.presenter.getVideo());
        assertEquals("before-dispatch", AppService.instance().getClientPlaybackNonce());
        assertTrue(fixture.lookups.isEmpty());
        assertTrue(fixture.played.isEmpty());
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals("prepared-nonce", AppService.instance().getClientPlaybackNonce());
        assertTrue(fixture.lookups.isEmpty());
        assertEquals(Collections.singletonList("first"), fixture.played);
        assertTrue(fixture.formatSubscription().isDisposed());
        fixture.presenter.onFinish();
    }

    @Test public void realPresenterRapidDispatchCannotDeliverQueuedFormatsToTheWrongVideo() throws Exception {
        PresenterFixture fixture = new PresenterFixture();
        fixture.presenter.onNewVideo(video("first"));
        Video second = video("second");
        fixture.presenter.onNewVideo(second);
        assertEquals(2, fixture.lookups.size());
        shadowOf(Looper.getMainLooper()).idle();
        assertSame(second, fixture.presenter.getVideo());
        assertEquals(Collections.singletonList("second"), fixture.played);
        fixture.presenter.onFinish();
    }

    private class PresenterFixture {
        final PlaybackPresenter presenter;
        final VideoLoaderController loader;
        final PlaybackView player;
        final Video old = video("old");
        final List<String> lookups = new ArrayList<>();
        final List<String> presenterVideoDuringLookup = new ArrayList<>();
        final List<String> played = new ArrayList<>();
        final List<Long> seeks = new ArrayList<>();
        Video next;

        @SuppressWarnings("unchecked")
        PresenterFixture() throws Exception {
            Constructor<PlaybackPresenter> constructor = PlaybackPresenter.class.getDeclaredConstructor(Context.class);
            constructor.setAccessible(true);
            presenter = constructor.newInstance(context);
            Field listenersField = PlaybackPresenter.class.getDeclaredField("mEventListeners");
            listenersField.setAccessible(true);
            List<PlayerEventListener> listeners = (List<PlayerEventListener>) listenersField.get(presenter);
            listeners.clear();
            loader = new VideoLoaderController() {
                @Override protected Observable<MediaItemFormatInfo> loadRegularFormatInfo(String id) {
                    lookups.add(id);
                    Video previous = presenter.getVideo();
                    presenterVideoDuringLookup.add(previous != null ? previous.videoId : null);
                    return Observable.just(format(id));
                }
            };
            listeners.add(loader); // Uses the real presenter's listener list and controller wiring.
            player = proxy(PlaybackView.class, (name, args) -> {
                if (name.equals("isEngineInitialized")) return true;
                if (name.equals("openUrlList")) played.add(presenter.getVideo().videoId);
                if (name.equals("setPositionMs")) seeks.add((Long) args[0]);
                return null;
            });
            Field playerField = PlaybackPresenter.class.getDeclaredField("mPlayer");
            playerField.setAccessible(true);
            playerField.set(presenter, new WeakReference<>(player));
            Field videoField = PlaybackPresenter.class.getDeclaredField("mVideo");
            videoField.setAccessible(true);
            videoField.set(presenter, new WeakReference<>(old));
            set(loader, "mSuggestionsController", new SuggestionsController() {
                @Override public Video getNext() { return next; }
            });
        }

        io.reactivex.disposables.Disposable formatSubscription() throws Exception {
            Field field = VideoLoaderController.class.getDeclaredField("mFormatInfoAction");
            field.setAccessible(true);
            return (io.reactivex.disposables.Disposable) field.get(loader);
        }
    }

    private MediaItemFormatInfo format(String id) {
        return proxy(MediaItemFormatInfo.class, (name, args) -> {
            if (name.equals("getVideoId")) return id;
            if (name.equals("containsUrlFormats") || name.equals("isCacheActual")) return true;
            if (name.equals("createUrlList")) return Collections.singletonList("https://example.invalid/synthetic");
            return null;
        });
    }

    private interface Calls { Object invoke(String method, Object[] arguments); }
    @SuppressWarnings("unchecked")
    private <T> T proxy(Class<T> type, Calls calls) {
        return (T) Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, (object, method, arguments) -> {
            Object result = calls.invoke(method.getName(), arguments);
            Class<?> resultType = method.getReturnType();
            if (result != null || !resultType.isPrimitive() || resultType == void.class) return result;
            if (resultType == boolean.class) return false;
            if (resultType == long.class) return 0L;
            if (resultType == float.class) return 0f;
            if (resultType == double.class) return 0d;
            return 0;
        });
    }

    private void startPreparation() {
        playing = true;
        duration = 10_000;
        controller.onPlay();
    }

    private Video video(String id) {
        Video video = new Video();
        video.videoId = id;
        video.isShorts = true;
        return video;
    }

    private void set(VideoLoaderController target, String name, Object value) throws Exception {
        Field field = VideoLoaderController.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(target, value);
    }

    private void loadFormats(VideoLoaderController target, Video video) throws Exception {
        Method method = VideoLoaderController.class.getDeclaredMethod("loadFormatInfo", Video.class);
        method.setAccessible(true);
        method.invoke(target, video);
    }
}
