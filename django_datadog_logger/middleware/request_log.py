import time
import logging
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        log_entry_dict = {"http.status_code": response.status_code}

        if hasattr(request, "request_start_time"):
            duration_seconds = time.time() - request.request_start_time
            log_entry_dict["duration"] = duration_seconds * 1000000000.0

        if 400 <= response.status_code < 500:
            log_entry_dict["error.kind"] = response.status_code
            log_entry_dict["error.message"] = response.reason_phrase
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
        return response

