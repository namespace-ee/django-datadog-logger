from functools import wraps

from django_datadog_logger.local import Local, release_local  # NOQA

local = Local()


def get_celery_request():
    try:
        return local.request
    except AttributeError:
        return None


def get_task_name(request):
    if hasattr(request, "task"):
        if isinstance(request.task, str):
            return request.task
        elif hasattr(request.task, "name"):
            return request.task.name
    return None


def store_celery_request(func):
    @wraps(func)
    def function_wrapper(*args, **kwargs):
        try:
            if args and hasattr(args[0], "request"):
                request = args[0].request
                if (type(request).__module__, type(request).__name__) == ("celery.app.task", "Context"):
                    local.request = request
            return func(*args, **kwargs)
        finally:
            release_local(local)

    return function_wrapper


__all__ = ["local", "get_celery_request", "store_celery_request"]
