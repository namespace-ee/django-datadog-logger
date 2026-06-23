"""Tests for the ``not_recursive`` re-entrancy guard."""

import inspect
import threading
from unittest.mock import patch

import pytest

from django_datadog_logger.recursion import RecursionDetected, not_recursive


class TestNotRecursive:
    def test_blocks_direct_recursion(self):
        """A guarded function that calls itself raises RecursionDetected
        instead of recursing — the contract the formatter relies on."""
        calls = []

        @not_recursive
        def recursive():
            calls.append(1)
            recursive()

        with pytest.raises(RecursionDetected):
            recursive()
        assert calls == [1]

    def test_blocks_indirect_recursion(self):
        """Re-entry through an intermediate call is also blocked — the real
        formatter scenario (helper -> logging -> formatter -> helper)."""

        @not_recursive
        def outer():
            def intermediate():
                outer()

            intermediate()

        with pytest.raises(RecursionDetected):
            outer()

    def test_allows_sequential_calls_including_after_an_error(self):
        """The in-flight flag is always cleared, so independent sequential
        calls keep working even after one raised."""

        @not_recursive
        def flaky(should_raise):
            if should_raise:
                raise ValueError("boom")
            return "ok"

        assert flaky(False) == "ok"
        with pytest.raises(ValueError):
            flaky(True)
        assert flaky(False) == "ok"

    def test_does_not_false_positive_on_unrelated_same_named_frame(self):
        """A non-recursive call must not be blocked just because an unrelated
        function sharing the guarded function's name is on the call stack.

        Two independently decorated functions both named ``helper`` — ``root``
        calls ``leaf`` exactly once. That is not recursion, but a guard that
        matches on frame *name* rather than actual re-entrancy raises
        RecursionDetected because ``root``'s frame (also named ``helper``) is
        still on the stack when ``leaf`` runs.
        """

        def make_guarded(body):
            @not_recursive
            def helper():
                return body()

            return helper

        leaf = make_guarded(lambda: "leaf-value")
        root = make_guarded(leaf)

        assert leaf.__name__ == root.__name__ == "helper"
        assert root() == "leaf-value"

    def test_does_not_walk_the_stack(self):
        """The guard must not call ``inspect.stack()`` — that resolved the
        source file of every frame on the stack, on every call, which is a
        per-call cost on the hot per-log-record logging path."""

        @not_recursive
        def guarded():
            return "ok"

        with patch.object(inspect, "stack") as stack:
            assert guarded() == "ok"
        stack.assert_not_called()

    def test_is_thread_local(self):
        """A call in flight on one thread must not make a concurrent call on
        another thread look re-entrant."""
        entered = threading.Event()
        release = threading.Event()
        results = {}

        @not_recursive
        def guarded(wait):
            if wait:
                entered.set()
                release.wait(timeout=5)
            return "ok"

        def run_worker():
            results["worker"] = guarded(wait=True)

        worker = threading.Thread(target=run_worker)
        worker.start()
        assert entered.wait(timeout=5)
        # `worker` holds the in-flight flag on its own thread; this call on the
        # main thread must still succeed.
        results["main"] = guarded(wait=False)
        release.set()
        worker.join(timeout=5)

        assert results == {"worker": "ok", "main": "ok"}
