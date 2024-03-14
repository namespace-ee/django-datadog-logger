import logging
import time

from rest_framework.utils.serializer_helpers import ReturnDict

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self.log_response(request, response)
        return response

    def process_response(self, request, response):
        self.log_response(request, response)
        return response

    def log_response(self, request, response):
        log_entry_dict = {"http.status_code": response.status_code}

        if hasattr(request, "request_start_time"):
            duration_seconds = getattr(response, "response_start_time", time.time()) - request.request_start_time
            log_entry_dict["duration"] = duration_seconds * 1000000000.0

        if 400 <= response.status_code < 500:
            log_entry_dict["error.kind"] = response.status_code
            log_entry_dict["error.message"] = response.reason_phrase
            if hasattr(response, "data") and isinstance(response.data, (list, dict, ReturnDict)):
                log_entry_dict["error.stack"] = response.data
            logger.warning(
                f"HTTP {response.status_code} {response.reason_phrase}",
                extra=log_entry_dict,
            )
        elif 500 <= response.status_code < 600:
            log_entry_dict["error.kind"] = response.status_code
            log_entry_dict["error.message"] = response.reason_phrase
            logger.error(
                f"HTTP {response.status_code} {response.reason_phrase}",
                extra=log_entry_dict,
            )
        else:
            logger.info(
                f"HTTP {response.status_code} {response.reason_phrase}",
                extra=log_entry_dict,
            )
