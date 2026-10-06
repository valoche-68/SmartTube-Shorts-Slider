package com.liskovsoft.smartyoutubetv2.common.misc;

import android.content.Context;
import android.os.Looper;
import com.liskovsoft.mediaserviceinterfaces.ContentService;
import com.liskovsoft.mediaserviceinterfaces.data.MediaGroup;
import com.liskovsoft.mediaserviceinterfaces.data.MediaItem;
import com.liskovsoft.sharedutils.prefs.GlobalPreferences;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.Playlist;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.SimpleMediaItem;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.Video;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.VideoGroup;
import com.liskovsoft.smartyoutubetv2.common.app.models.playback.controllers.SuggestionsController;
import com.liskovsoft.smartyoutubetv2.common.app.models.playback.controllers.VideoLoaderController;
import com.liskovsoft.smartyoutubetv2.common.app.models.playback.listener.PlayerEventListener;
import com.liskovsoft.smartyoutubetv2.common.app.views.PlaybackView;
import com.liskovsoft.smartyoutubetv2.common.prefs.PlayerTweaksData;
import io.reactivex.subjects.PublishSubject;
import io.reactivex.Observable;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class ShortsNavigationTest {
    private Context context;
    private TestSuggestions controller;
    private Video current;
    private List<VideoGroup> rows;
    private List<Video> results;
    private PublishSubject<MediaGroup> page;
    private AtomicInteger requests;

    @Before public void setup() throws Exception {
        context = RuntimeEnvironment.getApplication();
        GlobalPreferences.instance(context);
        Playlist.instance().clear();
        rows = new ArrayList<>();
        results = new ArrayList<>();
        current = video("current", true);
        current.isSynced = true;
        controller = new TestSuggestions();
        Playlist.instance().setCurrent(current);
        page = PublishSubject.create();
        requests = new AtomicInteger();
        ContentService service = proxy(ContentService.class, (method, arguments) -> {
            if (method.equals("continueGroupObserve")) {
                requests.incrementAndGet();
                return page;
            }
            return null;
        });
        field(controller, "mContentService", service);
        PlayerTweaksData.instance(context).setSectionPlaylistEnabled(false);
    }

    @Test public void sectionSettingDoesNotBlockHomeShortsAndMixedItemsAreSkipped() {
        Video longVideo = video("long", false);
        Video live = video("live", true);
        live.isLive = true;
        Video upcoming = video("upcoming", true);
        upcoming.isUpcoming = true;
        Video next = video("next", true);
        group(current, longVideo, live, upcoming, next);
        assertSame(next, controller.getNext());
        assertFalse(PlayerTweaksData.instance(context).isSectionPlaylistEnabled());
        PlayerTweaksData.instance(context).setShortsAutoScrollEnabled(false);
        assertSame(next, controller.getNext()); // Manual next still works while the Short loops.
    }

    @Test public void previousSkipsLongLiveAndUpcomingItemsInTheSourceAndQueue() {
        Video previous = video("previous", true);
        Video live = video("live", true);
        live.isLive = true;
        group(previous, video("long", false), live, current);
        assertSame(previous, controller.getPrevious());
        current.setGroup(null);
        Playlist.instance().clear();
        Playlist.instance().addAll(Arrays.asList(previous, video("long", false), live, current));
        Playlist.instance().setCurrent(current);
        assertSame(previous, controller.getPrevious());
        assertTrue(previous.fromQueue);
    }

    @Test public void queuedShortWinsOverQueuedLongVideo() {
        Video longVideo = video("queued_long", false);
        Video next = video("queued_short", true);
        Playlist.instance().addAll(Arrays.asList(current, longVideo, next));
        Playlist.instance().setCurrent(current);
        assertSame(next, controller.getNext());
        assertTrue(next.fromQueue);
    }

    @Test public void recommendationsFindActualShortInsteadOfFirstLongVideo() {
        Video longVideo = video("long", false);
        current.nextMediaItem = SimpleMediaItem.from(longVideo);
        Video next = video("next", true);
        rows.add(group(longVideo, next));
        assertSame(next, controller.getNext());
    }

    @Test public void currentAndAlreadyPlayedRecommendationsAreNotReplayed() {
        Video played = video("played", true);
        Playlist.instance().clear();
        Playlist.instance().addAll(Arrays.asList(played, current));
        Playlist.instance().setCurrent(current);
        rows.add(group(current, played, video("long", false)));
        current.setGroup(null); // These are recommendations, not the source-section order.
        assertNull(controller.getNext());
    }

    @Test public void sourceRowWrapperDoesNotRestartEarlierUnplayedShortsAtTheEnd() {
        Video earlier = video("earlier", true);
        VideoGroup source = group(earlier, current);
        VideoGroup wrapper = VideoGroup.from(source.getVideos());
        assertNotSame(source, wrapper);
        rows.add(wrapper);
        assertFalse(Playlist.instance().contains(earlier));
        assertNull(controller.getNext());
    }

    @Test public void regularVideoKeepsItsNativeNextRecommendation() {
        current = video("regular", false);
        Video next = video("next_long", false);
        current.nextMediaItem = SimpleMediaItem.from(next);
        assertEquals(next.videoId, controller.getNext().videoId);
    }

    @Test public void missingMetadataWaitsAndResolvesOnceSuggestionsArrive() {
        current.isSynced = false;
        controller.requestNextShort(results::add);
        assertTrue(results.isEmpty());
        Video next = video("next", true);
        rows.add(group(next));
        current.isSynced = true;
        controller.onMetadata(null);
        assertEquals(Arrays.asList(next), results);
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(16));
        assertEquals(1, results.size());
    }

    @Test public void endOfLoadedPageWaitsForNativeContinuation() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("page_one"));
        assertNull(controller.getNext());
        controller.requestNextShort(results::add);
        controller.requestNextShort(results::add);
        assertEquals(1, requests.get());
        assertTrue(results.isEmpty());
        Video next = video("next", true);
        page.onNext(mediaGroup(null, next));
        page.onComplete();
        assertEquals(Arrays.asList(next), results);
        assertEquals(next.videoId, controller.getNext().videoId);
    }

    @Test public void changingVideoCancelsContinuationWithoutOpeningOrMutatingOldPage() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("page_one"));
        controller.requestNextShort(results::add);
        assertTrue(page.hasObservers());
        current = video("replacement", true);
        controller.onNewVideo(current);
        assertFalse(page.hasObservers());
        page.onNext(mediaGroup(null, video("stale", true)));
        assertTrue(results.isEmpty());
        assertEquals(1, source.getSize());
    }

    @Test public void networkErrorReturnsConfirmedFailureOnlyOnce() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("page_one"));
        controller.requestNextShort(results::add);
        assertTrue(results.isEmpty());
        page.onError(new IllegalStateException("offline"));
        assertEquals(1, results.size());
        assertNull(results.get(0));
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(16));
        assertEquals(1, results.size());
    }

    @Test public void failedSourcePaginationUsesAVerifiedShortRecommendation() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("page_one"));
        Video fallback = video("fallback", true);
        rows.add(group(video("long", false), fallback));
        assertNull(controller.getNext()); // Preserve source order while its page is available.
        controller.requestNextShort(results::add);
        page.onError(new IllegalStateException("offline"));
        assertEquals(Arrays.asList(fallback), results);
    }

    @Test public void lightweightGroupCopyDoesNotBreakNextOrPrevious() {
        current.setGroup(group(current).copy());
        rows.add(group().copy());
        assertNull(controller.getNext());
        assertNull(controller.getPrevious());
    }

    @Test public void turningAutoOffWhilePaginationIsPendingPreventsAdvance() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("page_one"));
        List<Video> opened = new ArrayList<>();
        PlayerTweaksData.instance(context).setShortsAutoScrollEnabled(true);
        VideoLoaderController loader = loader(opened);
        automaticNext(loader);
        assertTrue(opened.isEmpty());
        PlayerTweaksData.instance(context).setShortsAutoScrollEnabled(false);
        page.onNext(mediaGroup(null, video("next", true)));
        assertTrue(opened.isEmpty());
        loader.loadNext(); // The same setting must still permit an explicit remote press.
        assertEquals(1, opened.size());
        assertEquals("next", opened.get(0).videoId);
    }

    @Test public void manualDownOverridesPendingAutoplayAfterAutoIsTurnedOff() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("page_one"));
        List<Video> opened = new ArrayList<>();
        PlayerTweaksData.instance(context).setShortsAutoScrollEnabled(true);
        VideoLoaderController loader = loader(opened);
        automaticNext(loader);
        assertEquals(1, requests.get());
        PlayerTweaksData.instance(context).setShortsAutoScrollEnabled(false);
        loader.loadNext();
        automaticNext(loader); // A repeated end event cannot override the explicit remote press.
        assertEquals(1, requests.get());
        assertTrue(opened.isEmpty());
        page.onNext(mediaGroup(null, video("next", true)));
        page.onComplete();
        assertEquals(1, opened.size());
        assertEquals("next", opened.get(0).videoId);
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(16));
        assertEquals(1, opened.size());
    }

    @Test public void repeatedContinuationTokenStopsWithoutAnInfiniteRetry() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("same_token"));
        controller.requestNextShort(results::add);
        page.onNext(mediaGroup("same_token", video("long", false)));
        assertEquals(1, requests.get());
        assertEquals(1, results.size());
        assertNull(results.get(0));
    }

    @Test public void synchronousFirstPageDoesNotLoseCancellationOfPendingSecondPage() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("first"));
        field(controller, "mContentService", proxy(ContentService.class, (method, arguments) -> {
            if (method.equals("continueGroupObserve")) {
                return requests.incrementAndGet() == 1 ?
                        Observable.just(mediaGroup("second", video("long", false))) : page;
            }
            return null;
        }));
        controller.requestNextShort(results::add);
        assertEquals(2, requests.get());
        assertTrue(page.hasObservers());
        current = video("replacement", true);
        controller.onNewVideo(current);
        assertFalse(page.hasObservers());
        page.onNext(mediaGroup(null, video("stale", true)));
        assertEquals(2, source.getSize());
        assertTrue(results.isEmpty());
    }

    @Test public void paginationStopsAfterTwoPagesWithoutAShort() throws Exception {
        VideoGroup source = group(current);
        field(source, "mMediaGroup", mediaGroup("first"));
        PublishSubject<MediaGroup> second = PublishSubject.create();
        field(controller, "mContentService", proxy(ContentService.class, (method, arguments) -> {
            if (method.equals("continueGroupObserve")) {
                return requests.incrementAndGet() == 1 ? page : second;
            }
            return null;
        }));
        controller.requestNextShort(results::add);
        page.onNext(mediaGroup("second", video("long_one", false)));
        assertEquals(2, requests.get());
        assertTrue(results.isEmpty());
        assertFalse(page.hasObservers());
        second.onNext(mediaGroup("third", video("long_two", false)));
        assertEquals(2, requests.get());
        assertEquals(1, results.size());
        assertNull(results.get(0));
        assertFalse(second.hasObservers());
    }

    @Test public void missingMetadataTimesOutAndFinishingCancelsTheTimeout() {
        current.isSynced = false;
        controller.requestNextShort(results::add);
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(16));
        assertEquals(1, results.size());
        assertNull(results.get(0));
        results.clear();
        controller.requestNextShort(results::add);
        controller.onFinish();
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(16));
        assertTrue(results.isEmpty());
    }

    private VideoLoaderController loader(List<Video> opened) throws Exception {
        VideoLoaderController loader = new VideoLoaderController() {
            @Override public PlaybackView getPlayer() { return controller.getPlayer(); }
            @Override public Video getVideo() { return current; }
            @Override public Context getContext() { return context; }
            @Override protected PlayerEventListener getMainController() {
                return proxy(PlayerEventListener.class, (method, arguments) -> {
                    if (method.equals("onNewVideo")) opened.add((Video) arguments[0]);
                    return null;
                });
            }
        };
        Field suggestions = VideoLoaderController.class.getDeclaredField("mSuggestionsController");
        suggestions.setAccessible(true);
        suggestions.set(loader, controller);

        return loader;
    }

    private void automaticNext(VideoLoaderController loader) throws Exception {
        Method loadNext = VideoLoaderController.class.getDeclaredMethod("loadNext", boolean.class);
        loadNext.setAccessible(true);
        loadNext.invoke(loader, true);
    }

    private Video video(String id, boolean shorts) {
        Video video = new Video();
        video.videoId = id;
        video.title = id;
        video.isShorts = shorts;
        return video;
    }

    private VideoGroup group(Video... videos) {
        return VideoGroup.from(new ArrayList<>(Arrays.asList(videos)));
    }

    private MediaGroup mediaGroup(String token, Video... videos) {
        List<MediaItem> items = new ArrayList<>();
        for (Video video : videos) {
            items.add(SimpleMediaItem.from(video));
        }
        return proxy(MediaGroup.class, (method, arguments) -> {
            switch (method) {
                case "getNextPageKey": return token;
                case "getMediaItems": return items;
                case "getType": return MediaGroup.TYPE_HOME;
                case "isEmpty": return items.isEmpty();
                default: return null;
            }
        });
    }

    private void field(Object target, String name, Object value) throws Exception {
        Field field = target instanceof SuggestionsController ? SuggestionsController.class.getDeclaredField(name) :
                target.getClass().getDeclaredField(name);
        field.setAccessible(true);
        field.set(target, value);
    }

    private interface Calls { Object invoke(String method, Object[] arguments); }

    @SuppressWarnings("unchecked")
    private <T> T proxy(Class<T> type, Calls calls) {
        return (T) Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, (object, method, arguments) -> {
            Object result = calls.invoke(method.getName(), arguments);
            if (result != null || !method.getReturnType().isPrimitive()) {
                return result;
            }
            if (method.getReturnType() == boolean.class) return false;
            if (method.getReturnType() == long.class) return 0L;
            if (method.getReturnType() == float.class) return 0f;
            if (method.getReturnType() == double.class) return 0d;
            if (method.getReturnType() == void.class) return null;
            return 0;
        });
    }

    private class TestSuggestions extends SuggestionsController {
        private final PlaybackView player = proxy(PlaybackView.class, (method, arguments) -> {
            if (method.equals("getSuggestionsByIndex")) {
                int index = (Integer) arguments[0];
                return index < rows.size() ? rows.get(index) : null;
            }
            return null;
        });
        @Override public PlaybackView getPlayer() { return player; }
        @Override public Video getVideo() { return current; }
        @Override public Context getContext() { return context; }
    }
}
