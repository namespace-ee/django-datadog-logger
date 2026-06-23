import threading
from functools import wraps


class RecursionDetected(RuntimeError):
    """function has been detected to be recursing"""


def not_recursive(f):
    """Raise :class:`RecursionDetected` if ``f`` is re-entered (directly or
    indirectly) while a call is already in progress on the same thread.

    Re-entrancy is tracked with a per-function thread-local flag. This is O(1)
    and, unlike the previous implementation, does not call ``inspect.stack()``
    on every call -- that walked the whole stack and resolved the source file
    of every frame, a measurable per-call cost on hot paths such as the
    per-log-record request introspection this decorator guards.

    The flag is bound to this specific function (the closure), so the guard
    triggers on actual re-entrancy only: an unrelated function that merely
    shares ``f``'s name no longer causes a false ``RecursionDetected``, and two
    distinct guarded functions with the same name no longer block each other.
    The thread-local scope keeps concurrent calls on different threads
    independent.
    """
    state = threading.local()

    @wraps(f)
    def wrapper(*args, **kwargs):
        if getattr(state, "in_flight", False):
            raise RecursionDetected(f"function '{f.__name__}' is recursive")
        state.in_flight = True
        try:
            return f(*args, **kwargs)
        finally:
            state.in_flight = False

    return wrapper
