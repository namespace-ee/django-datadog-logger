import logging

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.core.exceptions import BadRequest, PermissionDenied, SuspiciousOperation
from django.http import Http404
from django.http.multipartparser import MultiPartParserError

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware:
    async_capable = True
    sync_capable = True

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)
        if self.async_mode:
            markcoroutinefunction(self)

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)
        return self.get_response(request)

    async def __acall__(self, request):
        try:
            response = await self.get_response(request)
        except Exception as exc:
            self.process_exception(request, exc)
            raise
        return response

    def process_exception(self, request, exception):
        if isinstance(
            exception,
            (PermissionDenied, Http404, MultiPartParserError, BadRequest, SuspiciousOperation),
        ):
            return
        logger.exception(exception)

    def process_response(self, request, response):
        return response
