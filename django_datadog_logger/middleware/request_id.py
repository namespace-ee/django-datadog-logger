import re
import time
import uuid

from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from django_datadog_logger.wsgi import local


def generate_request_id():
    return str(uuid.uuid4())


def get_or_create_request_id(request):
    request_id = request.META.get("HTTP_X_REQUEST_ID")
    if request_id and re.match("^[a-zA-Z0-9+/=-]{20,200}$", request_id):
        return request_id
    else:
        return generate_request_id()


class RequestIdMiddleware:
    async_capable = True
    sync_capable = True

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)
        if self.async_mode:
            markcoroutinefunction(self)

    def _before_request(self, request):
        request.request_id = get_or_create_request_id(request)
        request.request_start_time = time.time()
        local.request = request

    def _after_request(self, request, response):
        response["X-Request-ID"] = request.request_id
        if hasattr(local, "request"):
            del local.request
        return response

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)
        self._before_request(request)
        response = self.get_response(request)
        return self._after_request(request, response)

    async def __acall__(self, request):
        self._before_request(request)
        response = await self.get_response(request)
        return self._after_request(request, response)
