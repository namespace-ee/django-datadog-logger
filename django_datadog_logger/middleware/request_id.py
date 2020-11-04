import re
import time
import uuid

from django_datadog_logger.wsgi import local
from django_datadog_logger.local import release_local


def generate_request_id():
    return str(uuid.uuid4())


def get_or_create_request_id(request):
    request_id = request.META.get("HTTP_X_REQUEST_ID")
    if request_id and re.match("^[a-zA-Z0-9+/=\-]{20,200}$", request_id):
        return request_id
    else:
        return generate_request_id()


class RequestIdMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = get_or_create_request_id(request)
        request.request_start_time = time.time()
        local.request = request
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        release_local(local)
        return response
