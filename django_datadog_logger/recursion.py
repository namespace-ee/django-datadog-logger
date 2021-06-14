from functools import wraps
import inspect


class RecursionDetected(RuntimeError):
    """function has been detected to be recursing"""


def not_recursive(f):
    """
    raise an exception if recursive
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        for frame in inspect.stack():
            if f.__name__ == frame.function:
                raise RecursionDetected(f"function '{f.__name__}' is recursive")

        return f(*args, **kwargs)

    return wrapper
