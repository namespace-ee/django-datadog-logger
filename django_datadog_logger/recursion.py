from functools import wraps

from asgiref.local import Local  # NOQA

_local = Local()


class RecursionDetected(RuntimeError):
    """function has been detected to be recursing"""


def not_recursive(f):
    """
    Raise RecursionDetected if ``f`` is re-entered within the same logical
    request/task context.

    Guards against the auth logging loop: accessing the lazy Django
    ``request.user`` triggers authentication, which logs, which formats the
    record and accesses ``request.user`` again. In-flight functions are tracked
    in an ``asgiref.local.Local`` set -- the same primitive the package already
    uses to scope the current request -- so the guard follows the request across
    thread and sync/async boundaries (WSGI, ASGI, Celery), and is keyed on the
    function's identity rather than its name.
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
