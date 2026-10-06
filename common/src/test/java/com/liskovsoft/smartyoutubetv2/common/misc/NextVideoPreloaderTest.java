package com.liskovsoft.smartyoutubetv2.common.misc;

import org.junit.Test;
import java.util.concurrent.atomic.AtomicInteger;
import io.reactivex.Observable;
import io.reactivex.subjects.PublishSubject;
import static org.junit.Assert.*;

public class NextVideoPreloaderTest {
    @Test
    public void cacheHitIsNotRequestedAgainUntilReset() {
        AtomicInteger calls = new AtomicInteger();
        NextVideoPreloader<String> preloader = new NextVideoPreloader<>(id -> {
            calls.incrementAndGet();
            return Observable.just(id);
        }, () -> 0, value -> true);
        preloader.prefetch("next");
        preloader.prefetch("next");
        assertEquals(1, calls.get());
        preloader.reset();
        preloader.prefetch("next");
        assertEquals(2, calls.get());
    }

    @Test
    public void pendingLookupIsDeduplicatedAndCancelledOnChangeOrExit() {
        PublishSubject<String> first = PublishSubject.create();
        PublishSubject<String> second = PublishSubject.create();
        AtomicInteger calls = new AtomicInteger();
        NextVideoPreloader<String> preloader = new NextVideoPreloader<>(id -> {
            calls.incrementAndGet();
            return "first".equals(id) ? first : second;
        }, () -> 0, value -> true);
        preloader.prefetch("first");
        preloader.prefetch("first");
        assertEquals(1, calls.get());
        assertTrue(first.hasObservers());
        preloader.prefetch("second");
        assertFalse(first.hasObservers());
        assertTrue(second.hasObservers());
        preloader.reset();
        assertFalse(second.hasObservers());
    }

    @Test
    public void failedAndEmptyLookupsRetryAfterBackoff() {
        for (boolean throwError : new boolean[]{false, true}) {
            AtomicInteger calls = new AtomicInteger();
            long[] clock = {0};
            NextVideoPreloader<String> preloader = new NextVideoPreloader<>(id -> {
                calls.incrementAndGet();
                if (throwError) throw new IllegalStateException("test");
                return Observable.empty();
            }, () -> clock[0], value -> true);
            preloader.prefetch("next");
            clock[0] = 14_999;
            preloader.prefetch("next");
            assertEquals(1, calls.get());
            clock[0] = 15_000;
            preloader.prefetch("next");
            assertEquals(2, calls.get());
        }
    }

    @Test
    public void invalidIdsAreIgnoredAndOnlyFirstResultIsNeeded() {
        PublishSubject<String> source = PublishSubject.create();
        NextVideoPreloader<String> preloader = new NextVideoPreloader<>(id -> source, () -> 0, value -> true);
        preloader.prefetch(null);
        preloader.prefetch("");
        assertFalse(source.hasObservers());
        preloader.prefetch("next");
        source.onNext("format");
        assertFalse(source.hasObservers());
        preloader.prefetch("next");
        assertFalse(source.hasObservers());
    }
    @Test
    public void onlyMatchingValidResultCanBeConsumedOnce() {
        boolean[] valid = {true};
        NextVideoPreloader<String> preloader = new NextVideoPreloader<>(Observable::just, () -> 0, value -> valid[0]);
        preloader.prefetch("next");
        assertEquals("next", preloader.take("next"));
        assertNull(preloader.take("next"));
        preloader.prefetch("next");
        assertNull(preloader.take("different"));
        preloader.prefetch("next");
        valid[0] = false;
        assertNull(preloader.take("next"));
    }
}
