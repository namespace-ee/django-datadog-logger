from functools import wraps

from celery import Task

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
            if args and isinstance(args[0], Task) and hasattr(args[0], "request"):
                local.request = {"id": args[0].request.id, "name": get_task_name(args[0].request)}
            return func(*args, **kwargs)
        finally:
            release_local(local)

    return function_wrapper


__all__ = ["local", "get_celery_request", "store_celery_request"]
