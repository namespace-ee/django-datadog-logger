import logging

from django.core.exceptions import PermissionDenied, BadRequest, SuspiciousOperation
from django.http import Http404
from django.http.multipartparser import MultiPartParserError
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):
        if isinstance(
                exception,
                (PermissionDenied, Http404, MultiPartParserError, BadRequest, SuspiciousOperation),
        ):
            return
        logger.exception(exception)

