package com.liskovsoft.smartyoutubetv2.common.misc;

import com.liskovsoft.mediaserviceinterfaces.data.MediaFormat;
import com.liskovsoft.mediaserviceinterfaces.data.MediaGroup;
import com.liskovsoft.mediaserviceinterfaces.data.MediaItem;
import com.liskovsoft.mediaserviceinterfaces.data.MediaItemFormatInfo;
import com.liskovsoft.sharedutils.helpers.Helpers;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.BrowseSection;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.SimpleMediaItem;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.Video;
import com.liskovsoft.smartyoutubetv2.common.app.models.data.VideoGroup;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class VideoShortsClassificationTest {
    @Test public void explicitShortsIdentitySurvivesBothVideoCopies() {
        Video original = video("short", true);
        assertTrue(Video.from(original).isShorts());
        assertTrue(original.copy().isShorts());
        Video ordinary = video("ordinary", false);
        assertFalse(Video.from(ordinary).isShorts());
        assertFalse(ordinary.copy().isShorts());
    }

    @Test public void mediaItemRoundTripRetainsIdentityEvenAfterGroupIsDetached() {
        Video original = video("short", true);
        MediaItem item = SimpleMediaItem.from(original);
        assertTrue(item.isShorts());
        Video restored = Video.from(item);
        restored.setGroup(null);
        assertTrue(restored.isShorts());
        assertFalse(SimpleMediaItem.from(video("ordinary", false)).isShorts());
    }

    @Test public void nativeMediaItemProofIsRetainedByVideoCopies() {
        Video original = video("short", false);
        original.mediaItem = SimpleMediaItem.from(video("short", true));
        assertTrue(original.isShorts());
        assertTrue(Video.from(original).isShorts());
        assertTrue(original.copy().isShorts());
        assertTrue(Video.fromString(original.toString()).isShorts());
    }

    @Test public void dedicatedSectionProofSurvivesGroupLossAndCopies() {
        BrowseSection section = new BrowseSection(MediaGroup.TYPE_SHORTS, "Shorts", BrowseSection.TYPE_SHORTS_GRID, 0);
        VideoGroup group = VideoGroup.from(section);
        // The media row's type may differ from the dedicated browse section's type.
        group.setType(MediaGroup.TYPE_HOME);
        Video original = video("section-short", false);
        original.setGroup(group);
        assertTrue(original.isShorts());
        assertTrue(Video.from(original).isShorts());
        assertTrue(original.copy().isShorts());
        original.setGroup(null);
        assertTrue(original.isShorts());
        assertTrue(Video.from(SimpleMediaItem.from(original)).isShorts());
    }

    @Test public void dedicatedMediaGroupIsProofWithoutItemFlag() {
        VideoGroup group = VideoGroup.from(new ArrayList<Video>());
        group.setType(MediaGroup.TYPE_SHORTS);
        Video original = video("section-short", false);
        original.setGroup(group);
        assertTrue(original.isShorts());
        original.setGroup(null);
        assertTrue(original.copy().isShorts());
    }

    @Test public void ninthOrdinaryVideoIsNotMarkedByFirstEightShorts() {
        List<Video> videos = new ArrayList<>();
        for (int i = 0; i < 8; i++) videos.add(video("short-" + i, true));
        Video ordinary = video("ordinary", false);
        videos.add(ordinary);
        VideoGroup group = VideoGroup.from(videos);
        assertTrue(group.isShorts()); // The grid's presentation samples the first eight items.
        assertFalse(ordinary.isShorts());
        assertFalse(Video.from(ordinary).isShorts());
        assertFalse(ordinary.copy().isShorts());
        assertFalse(Video.from(SimpleMediaItem.from(ordinary)).isShorts());
    }

    @Test public void serializationRetainsShortsAndReadsOldTwentyThreeFieldFormat() {
        Video original = video("short", true);
        original.title = "Title with separators | #";
        Video restored = Video.fromString(original.toString());
        assertNotNull(restored);
        assertEquals(original.videoId, restored.videoId);
        assertEquals(original.title, restored.title);
        assertTrue(restored.isShorts());
        String[] legacy = Arrays.copyOf(Helpers.splitObj(original.toString()), 23);
        Video old = Video.fromString(Helpers.mergeObj((Object[]) legacy));
        assertNotNull(old);
        assertEquals(original.videoId, old.videoId);
        assertFalse(old.isShorts()); // Missing source metadata must not be guessed.
        assertFalse(Video.fromString(video("ordinary", false).toString()).isShorts());
    }

    @Test public void portraitVideoFormatsAloneDoNotIdentifyShorts() {
        MediaFormat portrait = (MediaFormat) Proxy.newProxyInstance(MediaFormat.class.getClassLoader(),
                new Class<?>[]{MediaFormat.class}, (proxy, method, args) -> {
                    if ("getWidth".equals(method.getName())) return 1080;
                    if ("getHeight".equals(method.getName())) return 1920;
                    return defaultValue(method.getReturnType());
                });
        MediaItemFormatInfo format = (MediaItemFormatInfo) Proxy.newProxyInstance(MediaItemFormatInfo.class.getClassLoader(),
                new Class<?>[]{MediaItemFormatInfo.class}, (proxy, method, args) -> {
                    if ("getAdaptiveFormats".equals(method.getName())) return Collections.singletonList(portrait);
                    if ("getLengthSeconds".equals(method.getName())) return "3600";
                    return defaultValue(method.getReturnType());
                });
        Video ordinary = video("vertical-long-video", false);
        ordinary.sync(format);
        assertFalse(ordinary.isShorts());
        assertFalse(ordinary.copy().isShorts());
    }

    @Test public void liveVideoDoesNotReceiveShortsBehaviorFromItsSection() {
        VideoGroup group = VideoGroup.from(new ArrayList<Video>());
        group.setType(MediaGroup.TYPE_SHORTS);
        Video live = video("live", false);
        live.isLive = true;
        live.setGroup(group);
        assertFalse(live.isShorts());
        assertFalse(SimpleMediaItem.from(live).isShorts());
        assertFalse(Video.fromString(live.toString()).isShorts());
    }

    private static Video video(String id, boolean shorts) {
        Video video = new Video();
        video.videoId = id;
        video.isShorts = shorts;
        return video;
    }

    private static Object defaultValue(Class<?> type) {
        if (type == boolean.class) return false;
        if (type == int.class) return 0;
        if (type == long.class) return 0L;
        if (type == float.class) return 0f;
        return null;
    }
}
