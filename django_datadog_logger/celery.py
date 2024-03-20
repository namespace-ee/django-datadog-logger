from functools import wraps

from asgiref.local import Local


local = Local()


def get_celery_request():
    return getattr(local, "request", None)


def get_task_name(request):
    try:
        return request.task.name
    except AttributeError:
        try:
            return str(request.task)
        except AttributeError:
            return None


def store_celery_request(func):
    @wraps(func)
    def function_wrapper(*args, **kwargs):
        if args and hasattr(args[0], "request"):
            request = args[0].request
            if (type(request).__module__, type(request).__name__) == ("celery.app.task", "Context"):
                local.request = request
        return func(*args, **kwargs)


    return function_wrapper


__all__ = ["local", "get_celery_request", "store_celery_request"]
