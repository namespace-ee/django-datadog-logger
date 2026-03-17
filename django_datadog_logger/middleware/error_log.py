import logging

from django.core.exceptions import BadRequest, PermissionDenied, SuspiciousOperation
from django.http import Http404
from django.http.multipartparser import MultiPartParserError

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(
            exception,
            (PermissionDenied, Http404, MultiPartParserError, BadRequest, SuspiciousOperation),
        ):
            return
        logger.exception(exception)

    def process_response(self, request, response):
        return response
