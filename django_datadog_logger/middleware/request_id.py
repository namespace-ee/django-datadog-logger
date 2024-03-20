import time
import uuid

from django.utils.deprecation import MiddlewareMixin
from django_datadog_logger.wsgi import local


def generate_request_id():
    return str(uuid.uuid4())


def get_or_create_request_id(request):
    request_id = request.META.get("HTTP_X_REQUEST_ID")
    return request_id or generate_request_id()


class RequestIdMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.request_id = get_or_create_request_id(request)
        request.request_start_time = time.time()
        local.request = request

    def process_response(self, request, response):
        response["X-Request-ID"] = request.request_id
        return response

