from functools import wraps

from asgiref.local import Local  # NOQA

_local = Local()


class RecursionDetected(RuntimeError):
    """function has been detected to be recursing"""


def not_recursive(f):
    """
    Raise RecursionDetected if ``f`` is re-entered within the same logical
    request/task context.

    This is a *safety* guard against the auth logging loop: accessing the lazy
    Django ``request.user`` triggers authentication, which logs, which formats
    the record and accesses ``request.user`` again -- an unbounded loop. Because
    a missed loop is catastrophic (runaway recursion) while an over-eager stop
    is benign (the formatter catches RecursionDetected and drops the user from a
    single record), the guard is deliberately biased to fail safe.

    In-flight functions are tracked in an ``asgiref.local.Local`` set, keyed on
    the function's identity rather than its name. ``Local`` is chosen -- over a
    plain ``threading.local`` -- because the request itself is resolved through
    ``asgiref.local.Local`` (see ``wsgi.py``): under ASGI a single request may be
    handled across the event-loop thread and ``sync_to_async`` executor threads,
    so an auth loop can cross the sync/async boundary while staying within one
    request. Scoping the guard the same way the request is scoped means such a
    loop is still caught, whereas a thread-local flag set on one thread would not
    be seen on another and the loop would slip through. asgiref propagates the
    context across that boundary, so any deviation is toward over-firing (the
    safe direction), never toward missing a loop.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            in_flight = _local.in_flight
        except AttributeError:
            in_flight = _local.in_flight = set()
        if f in in_flight:
            raise RecursionDetected(f"function '{f.__name__}' is recursive")
        in_flight.add(f)
        try:
            return f(*args, **kwargs)
        finally:
            in_flight.discard(f)

    return wrapper
