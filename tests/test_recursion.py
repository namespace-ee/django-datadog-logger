"""Tests for the `not_recursive` re-entrancy guard."""

import inspect
import threading
from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync, sync_to_async

from django_datadog_logger.recursion import RecursionDetected, not_recursive


def test_true_self_recursion_is_detected():
    """A function that calls itself is stopped by the guard."""

    @not_recursive
    def recurse(n):
        return recurse(n - 1)

    with pytest.raises(RecursionDetected):
        recurse(5)


def test_indirect_recursion_is_detected():
    """Re-entry through an intermediate call is blocked -- the real formatter
    scenario (helper -> logging -> formatter -> helper)."""

    @not_recursive
    def outer():
        def intermediate():
            outer()

        intermediate()

    with pytest.raises(RecursionDetected):
        outer()


def test_detects_recursion_across_async_boundary():
    """Re-entry that crosses a sync -> async -> sync hop within one request is
    still caught.

    This is the ASGI case the guard exists for: under ASGI a single request is
    handled across the event-loop thread and ``sync_to_async`` executor threads,
    so an auth loop can re-enter the guarded function on a *different* thread
    while staying in the same request. Because the marker lives in an
    ``asgiref.local.Local`` (which asgiref propagates across the boundary) rather
    than in a thread-local, the in-flight marker set before the hop is visible
    after it, and the loop is detected. A plain ``threading.local`` guard, bound
    to the original thread, would not see it.
    """
    outer_thread = {}
    boundary_thread = {}

    @not_recursive
    def guarded(reenter):
        if not reenter:
            return "leaf"
        outer_thread["id"] = threading.get_ident()

        async def bridge():
            def reenter_guarded():
                boundary_thread["id"] = threading.get_ident()
                return guarded(reenter=False)  # re-entry -> must be blocked

            # thread_sensitive=False forces a distinct executor thread.
            return await sync_to_async(reenter_guarded, thread_sensitive=False)()

        return async_to_sync(bridge)()

    with pytest.raises(RecursionDetected):
        guarded(reenter=True)

    # The re-entry genuinely happened on another thread; the guard caught it
    # anyway because it is scoped like the request, not like the thread.
    assert boundary_thread["id"] != outer_thread["id"]


def test_does_not_walk_the_stack():
    """The guard must not call ``inspect.stack()`` -- that resolved the source
    file of every frame on every call, a per-call cost on the hot logging
    path."""

    @not_recursive
    def guarded():
        return "ok"

    with patch.object(inspect, "stack") as stack:
        assert guarded() == "ok"
    stack.assert_not_called()


def test_single_call_returns_normally():
    """A non-recursive call returns its value and leaves no state behind."""

    @not_recursive
    def once():
        return "value"

    assert once() == "value"
    # State is cleared, so a second independent call also succeeds.
    assert once() == "value"


def test_unrelated_same_named_functions_do_not_block():
    """
    Regression for issue #52: matching on identity, not name.

    Two independently decorated functions that share a name must not block
    each other when one calls the other.
    """

    def make_guarded(body):
        @not_recursive
        def helper():
            return body()

        return helper

    leaf = make_guarded(lambda: "leaf-value")
    root = make_guarded(leaf)  # different function, same name "helper"

    assert root() == "leaf-value"


def test_two_guarded_functions_call_each_other_in_one_context():
    """Distinct guarded functions may nest within the same context."""

    @not_recursive
    def inner():
        return "inner"

    @not_recursive
    def outer():
        return inner()

    assert outer() == "inner"


def test_flag_cleared_after_exception():
    """A raising call still clears its in-flight marker (finally)."""

    @not_recursive
    def boom():
        raise ValueError("kaboom")

    with pytest.raises(ValueError):
        boom()
    # If the marker leaked, this second call would raise RecursionDetected.
    with pytest.raises(ValueError):
        boom()


def test_concurrent_threads_are_isolated():
    """
    A function in flight on one thread must not trip the guard on another.

    Uses barriers so both threads are provably inside the guarded function at
    the same time, then asserts neither observed a RecursionDetected.
    """

    both_inside = threading.Barrier(2)
    errors = []

    @not_recursive
    def guarded():
        try:
            both_inside.wait(timeout=5)
        except RecursionDetected as exc:  # pragma: no cover - failure path
            errors.append(exc)
        return "ok"

    def run():
        try:
            guarded()
        except RecursionDetected as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
