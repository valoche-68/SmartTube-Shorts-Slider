package com.liskovsoft.smartyoutubetv2.common.misc;

import io.reactivex.Observable;
import io.reactivex.disposables.SerialDisposable;
import io.reactivex.subjects.ReplaySubject;
import java.util.concurrent.atomic.AtomicBoolean;

/** One cancellable lookup, retained until consumed. Called on the UI thread. */
public final class NextVideoPreloader<T> {
    private static final long RETRY_DELAY_MS = 15_000;
    public interface Loader<T> { Observable<T> load(String videoId); }
    public interface Clock { long now(); }
    public interface Validator<T> { boolean valid(T value); }
    public interface Observer { void event(String event, long elapsedMs); }
    private final Loader<T> loader;
    private final Clock clock;
    private final Validator<T> validator;
    private final Observer observer;
    private Lookup<T> lookup;

    private static final class Lookup<T> {
        final String videoId;
        final SerialDisposable request = new SerialDisposable();
        final ReplaySubject<T> completion = ReplaySubject.createWithSize(1);
        boolean running = true;
        T result;
        long retryAt;
        long started;
        Lookup(String videoId) { this.videoId = videoId; }
    }

    public NextVideoPreloader(Loader<T> loader, Clock clock, Validator<T> validator) {
        this(loader, clock, validator, (event, elapsedMs) -> {});
    }

    public NextVideoPreloader(Loader<T> loader, Clock clock, Validator<T> validator, Observer observer) {
        this.loader = loader;
        this.clock = clock;
        this.validator = validator;
        this.observer = observer;
    }

    public void prefetch(String id) {
        if (id == null || id.isEmpty()) return;
        if (lookup != null && id.equals(lookup.videoId) &&
                (lookup.running || (lookup.result != null && validator.valid(lookup.result)) || clock.now() < lookup.retryAt)) return;
        reset();
        Lookup<T> pending = new Lookup<>(id);
        lookup = pending;
        pending.started = clock.now();
        event("prepare_start", pending);
        pending.request.set(Observable.defer(() -> loader.load(id)).take(1).subscribe(
                value -> {
                    if (!pending.request.isDisposed() && validator.valid(value)) {
                        pending.result = value;
                        finish(pending);
                        event("prepare_ready", pending);
                        pending.completion.onNext(value);
                    }
                }, error -> {
                    finish(pending);
                    if (!pending.request.isDisposed()) {
                        event("prepare_error", pending);
                        pending.completion.onError(error);
                    }
                }, () -> {
                    finish(pending);
                    if (!pending.request.isDisposed()) {
                        if (pending.result == null) event("prepare_empty", pending);
                        pending.completion.onComplete();
                    }
                }));
    }

    /** Consume a completed result, or transfer a matching pending request to its single foreground subscriber. */
    public Observable<T> consume(String id) {
        Lookup<T> pending = lookup;
        if (id == null || pending == null || !id.equals(pending.videoId)) {
            reset();
            observer.event("consume_miss", 0);
            return null;
        }
        if (pending.result != null && validator.valid(pending.result)) {
            T value = pending.result;
            event("consume_hit", pending);
            reset();
            return once(Observable.just(value).filter(validator::valid));
        }
        if (!pending.running) {
            reset();
            observer.event("consume_miss", 0);
            return null;
        }
        event("consume_pending", pending);
        lookup = null; // The foreground subscription now owns cancellation of this lookup.
        return once(pending.completion.take(1).filter(validator::valid).doFinally(() -> {
            if (pending.running) event("foreground_cancel", pending);
            pending.request.dispose();
        }));
    }

    private Observable<T> once(Observable<T> source) {
        AtomicBoolean subscribed = new AtomicBoolean();
        return Observable.defer(() -> subscribed.compareAndSet(false, true) ? source : Observable.empty());
    }

    public T take(String id) {
        T value = lookup != null && id != null && id.equals(lookup.videoId) && lookup.result != null &&
                validator.valid(lookup.result) ? lookup.result : null;
        reset();
        return value;
    }

    private void finish(Lookup<T> pending) {
        pending.running = false;
        pending.retryAt = clock.now() + RETRY_DELAY_MS;
    }

    private void event(String name, Lookup<T> pending) {
        observer.event(name, Math.max(0, clock.now() - pending.started));
    }

    public void reset() {
        if (lookup != null) {
            if (lookup.running) event("prepare_cancel", lookup);
            lookup.request.dispose();
        }
        lookup = null;
    }
}
