from asgiref.local import Local

local = Local()


def get_asgi_request():
    try:
        return local.request
    except AttributeError:
        return None


__all__ = ["local", "get_asgi_request"]
