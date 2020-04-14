import time
import uuid

from django_datadog_logger.wsgi import local
from django_datadog_logger.local import release_local


def generate_request_id():
    return str(uuid.uuid4())


class RequestIdMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = generate_request_id()
        request.request_start_time = time.time()
        local.request = request
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        release_local(local)
        return response
