"""Tests for async middleware support."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from asgiref.sync import iscoroutinefunction
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse

from django_datadog_logger.middleware.error_log import ErrorLoggingMiddleware
from django_datadog_logger.middleware.request_id import RequestIdMiddleware
from django_datadog_logger.middleware.request_log import RequestLoggingMiddleware


class RequestIdMiddlewareSyncTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure()

    def test_sync_call(self):
        response = HttpResponse()
        get_response = MagicMock(return_value=response)
        middleware = RequestIdMiddleware(get_response)

        request = MagicMock()
        request.META = {}
        result = middleware(request)

        self.assertEqual(result, response)
        self.assertTrue(hasattr(request, "request_id"))
        self.assertTrue(hasattr(request, "request_start_time"))
        self.assertEqual(result["X-Request-ID"], request.request_id)

    def test_sync_preserves_existing_request_id(self):
        response = HttpResponse()
        get_response = MagicMock(return_value=response)
        middleware = RequestIdMiddleware(get_response)

        request = MagicMock()
        request.META = {"HTTP_X_REQUEST_ID": "a" * 20}
        middleware(request)

        self.assertEqual(request.request_id, "a" * 20)

    def test_not_marked_as_coroutine_for_sync(self):
        get_response = MagicMock()
        middleware = RequestIdMiddleware(get_response)
        self.assertFalse(iscoroutinefunction(middleware))


class RequestIdMiddlewareAsyncTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure()

    def test_marked_as_coroutine_for_async(self):
        async_response = AsyncMock(return_value=HttpResponse())
        middleware = RequestIdMiddleware(async_response)
        self.assertTrue(iscoroutinefunction(middleware))

    def test_async_call_via_dunder_call(self):
        """Test that __call__ delegates to __acall__ when in async mode."""
        response = HttpResponse()
        get_response = AsyncMock(return_value=response)
        middleware = RequestIdMiddleware(get_response)

        request = MagicMock()
        request.META = {}

        # __call__ should return a coroutine when in async mode
        result = asyncio.run(middleware(request))

        self.assertEqual(result, response)
        self.assertTrue(hasattr(request, "request_id"))
        self.assertTrue(hasattr(request, "request_start_time"))
        self.assertEqual(result["X-Request-ID"], request.request_id)

    def test_async_preserves_existing_request_id(self):
        response = HttpResponse()
        get_response = AsyncMock(return_value=response)
        middleware = RequestIdMiddleware(get_response)

        request = MagicMock()
        request.META = {"HTTP_X_REQUEST_ID": "b" * 20}

        asyncio.run(middleware(request))

        self.assertEqual(request.request_id, "b" * 20)


class ErrorLoggingMiddlewareSyncTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure()

    def test_sync_call(self):
        response = HttpResponse()
        get_response = MagicMock(return_value=response)
        middleware = ErrorLoggingMiddleware(get_response)

        result = middleware(MagicMock())
        self.assertEqual(result, response)

    def test_process_exception_ignores_expected_exceptions(self):
        middleware = ErrorLoggingMiddleware(MagicMock())
        with patch("django_datadog_logger.middleware.error_log.logger") as mock_logger:
            middleware.process_exception(MagicMock(), Http404())
            middleware.process_exception(MagicMock(), PermissionDenied())
            mock_logger.exception.assert_not_called()

    def test_process_exception_logs_unexpected_exceptions(self):
        middleware = ErrorLoggingMiddleware(MagicMock())
        with patch("django_datadog_logger.middleware.error_log.logger") as mock_logger:
            exc = RuntimeError("unexpected")
            middleware.process_exception(MagicMock(), exc)
            mock_logger.exception.assert_called_once_with(exc)

    def test_not_marked_as_coroutine_for_sync(self):
        get_response = MagicMock()
        middleware = ErrorLoggingMiddleware(get_response)
        self.assertFalse(iscoroutinefunction(middleware))


class ErrorLoggingMiddlewareAsyncTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure()

    def test_marked_as_coroutine_for_async(self):
        get_response = AsyncMock(return_value=HttpResponse())
        middleware = ErrorLoggingMiddleware(get_response)
        self.assertTrue(iscoroutinefunction(middleware))

    def test_async_call_success(self):
        response = HttpResponse()
        get_response = AsyncMock(return_value=response)
        middleware = ErrorLoggingMiddleware(get_response)

        result = asyncio.run(middleware(MagicMock()))
        self.assertEqual(result, response)

    def test_async_call_logs_unexpected_exception(self):
        exc = RuntimeError("unexpected")
        get_response = AsyncMock(side_effect=exc)
        middleware = ErrorLoggingMiddleware(get_response)

        with patch("django_datadog_logger.middleware.error_log.logger") as mock_logger:
            with self.assertRaises(RuntimeError):
                asyncio.run(middleware(MagicMock()))
            mock_logger.exception.assert_called_once_with(exc)

    def test_async_call_ignores_expected_exception(self):
        get_response = AsyncMock(side_effect=Http404())
        middleware = ErrorLoggingMiddleware(get_response)

        with patch("django_datadog_logger.middleware.error_log.logger") as mock_logger:
            with self.assertRaises(Http404):
                asyncio.run(middleware(MagicMock()))
            mock_logger.exception.assert_not_called()


class RequestLoggingMiddlewareSyncTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure()

    def test_sync_call(self):
        response = HttpResponse()
        get_response = MagicMock(return_value=response)
        middleware = RequestLoggingMiddleware(get_response)

        request = MagicMock()
        request.request_start_time = 1000.0
        with patch("django_datadog_logger.middleware.request_log.logger"):
            result = middleware(request)
        self.assertEqual(result, response)

    def test_not_marked_as_coroutine_for_sync(self):
        get_response = MagicMock()
        middleware = RequestLoggingMiddleware(get_response)
        self.assertFalse(iscoroutinefunction(middleware))

    def test_logs_2xx_as_info(self):
        response = HttpResponse(status=200)
        get_response = MagicMock(return_value=response)
        middleware = RequestLoggingMiddleware(get_response)

        request = MagicMock(spec=[])
        with patch("django_datadog_logger.middleware.request_log.logger") as mock_logger:
            middleware(request)
            mock_logger.info.assert_called_once()
            mock_logger.warning.assert_not_called()
            mock_logger.error.assert_not_called()

    def test_logs_4xx_as_warning(self):
        response = HttpResponse(status=400)
        get_response = MagicMock(return_value=response)
        middleware = RequestLoggingMiddleware(get_response)

        request = MagicMock(spec=[])
        with patch("django_datadog_logger.middleware.request_log.logger") as mock_logger:
            middleware(request)
            mock_logger.warning.assert_called_once()
            call_kwargs = mock_logger.warning.call_args
            self.assertEqual(call_kwargs.kwargs["extra"]["error.kind"], 400)

    def test_logs_5xx_as_error(self):
        response = HttpResponse(status=500)
        get_response = MagicMock(return_value=response)
        middleware = RequestLoggingMiddleware(get_response)

        request = MagicMock(spec=[])
        with patch("django_datadog_logger.middleware.request_log.logger") as mock_logger:
            middleware(request)
            mock_logger.error.assert_called_once()
            call_kwargs = mock_logger.error.call_args
            self.assertEqual(call_kwargs.kwargs["extra"]["error.kind"], 500)

    def test_logs_duration_when_request_start_time_present(self):
        response = HttpResponse(status=200)
        get_response = MagicMock(return_value=response)
        middleware = RequestLoggingMiddleware(get_response)

        request = MagicMock(spec=["request_start_time"])
        request.request_start_time = 1000.0
        with patch("django_datadog_logger.middleware.request_log.logger") as mock_logger:
            middleware(request)
            call_kwargs = mock_logger.info.call_args
            self.assertIn("duration", call_kwargs.kwargs["extra"])

    def test_no_duration_when_request_start_time_absent(self):
        response = HttpResponse(status=200)
        get_response = MagicMock(return_value=response)
        middleware = RequestLoggingMiddleware(get_response)

        request = MagicMock(spec=[])
        with patch("django_datadog_logger.middleware.request_log.logger") as mock_logger:
            middleware(request)
            call_kwargs = mock_logger.info.call_args
            self.assertNotIn("duration", call_kwargs.kwargs["extra"])


class RequestLoggingMiddlewareAsyncTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure()

    def test_marked_as_coroutine_for_async(self):
        get_response = AsyncMock(return_value=HttpResponse())
        middleware = RequestLoggingMiddleware(get_response)
        self.assertTrue(iscoroutinefunction(middleware))

    def test_async_call(self):
        response = HttpResponse()
        get_response = AsyncMock(return_value=response)
        middleware = RequestLoggingMiddleware(get_response)

        request = MagicMock()
        request.request_start_time = 1000.0
        with patch("django_datadog_logger.middleware.request_log.logger"):
            result = asyncio.run(middleware(request))
        self.assertEqual(result, response)

    def test_async_logs_response(self):
        response = HttpResponse(status=201)
        get_response = AsyncMock(return_value=response)
        middleware = RequestLoggingMiddleware(get_response)

        request = MagicMock(spec=[])
        with patch("django_datadog_logger.middleware.request_log.logger") as mock_logger:
            asyncio.run(middleware(request))
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args
            self.assertEqual(call_kwargs.kwargs["extra"]["http.status_code"], 201)


class MiddlewareCapabilityTestCase(unittest.TestCase):
    """Test that middleware classes declare async/sync capability."""

    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure()

    def test_request_id_middleware_capabilities(self):
        self.assertTrue(RequestIdMiddleware.async_capable)
        self.assertTrue(RequestIdMiddleware.sync_capable)

    def test_error_logging_middleware_capabilities(self):
        self.assertTrue(ErrorLoggingMiddleware.async_capable)
        self.assertTrue(ErrorLoggingMiddleware.sync_capable)

    def test_request_logging_middleware_capabilities(self):
        self.assertTrue(RequestLoggingMiddleware.async_capable)
        self.assertTrue(RequestLoggingMiddleware.sync_capable)
