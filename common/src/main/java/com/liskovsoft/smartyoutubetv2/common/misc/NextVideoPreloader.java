package com.liskovsoft.smartyoutubetv2.common.misc;

import io.reactivex.Observable;
import io.reactivex.disposables.SerialDisposable;

/** One cancellable lookup, retained until consumed. Called on the UI thread. */
public final class NextVideoPreloader<T> {
    private static final long RETRY_DELAY_MS = 15_000;
    public interface Loader<T> { Observable<T> load(String videoId); }
    public interface Clock { long now(); }
    public interface Validator<T> { boolean valid(T value); }
    private final Loader<T> loader;
    private final Clock clock;
    private final Validator<T> validator;
    private final SerialDisposable request = new SerialDisposable();
    private String videoId;
    private boolean running;
    private T result;
    private long retryAt;
    private int generation;

    public NextVideoPreloader(Loader<T> loader, Clock clock, Validator<T> validator) {
        this.loader = loader;
        this.clock = clock;
        this.validator = validator;
    }

    public void prefetch(String id) {
        if (id == null || id.isEmpty()) return;
        if (id.equals(videoId) && (running || (result != null && validator.valid(result)) || clock.now() < retryAt)) return;
        reset();
        videoId = id;
        running = true;
        int token = generation;
        request.set(Observable.defer(() -> loader.load(id)).take(1).subscribe(
                value -> { if (token == generation && validator.valid(value)) result = value; },
                error -> finish(token), () -> finish(token)));
    }

    public T take(String id) {
        T value = id != null && id.equals(videoId) && result != null && validator.valid(result) ? result : null;
        reset();
        return value;
    }

    private void finish(int token) {
        if (token == generation) {
            running = false;
            retryAt = clock.now() + RETRY_DELAY_MS;
        }
    }

    public void reset() {
        generation++;
        request.set(null);
        videoId = null;
        running = false;
        result = null;
        retryAt = 0;
    }
}
