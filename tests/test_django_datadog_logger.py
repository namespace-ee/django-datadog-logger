"""Tests for `django_datadog_logger` package."""

import collections.abc
import logging
from unittest.mock import patch

import pytest

import django_datadog_logger.wsgi
from django_datadog_logger.formatters.datadog import DatadogJSONFormatter

urlpatterns = []


class TestDjangoDatadogLogger:
    def test_format_json_accepts_a_tuple_of_nones_as_exc_info(self):
        """
        When logger is called with exc_info=True, then the exc_info
        attribute of the LogRecord is a tuple of (None, None, None).
        """
        record = logging.LogRecord("foo", logging.ERROR, "foo.py", 42, "This is an error", None, (None, None, None))
        formatter = DatadogJSONFormatter()
        json_record = formatter.json_record("Foo", {}, record)

        assert json_record.get("error.kind") is None


class JWTCredentialsLike(collections.abc.Mapping):
    """Read-only Mapping that is not a dict, like rest_framework_sso JWTCredentials."""

    def __init__(self, payload):
        self._payload = payload

    def __getitem__(self, key):
        return self._payload[key]

    def __iter__(self):
        return iter(self._payload)

    def __len__(self):
        return len(self._payload)


class TestRequestAuth:
    @pytest.fixture(autouse=True)
    def urlconf(self, settings):
        settings.ROOT_URLCONF = __name__

    def format_with_auth(self, rf, auth):
        request = rf.get("/")
        request.auth = auth
        record = logging.LogRecord("foo", logging.INFO, "foo.py", 42, "Hello", None, None)
        with patch.object(django_datadog_logger.wsgi.local, "request", request, create=True):
            return DatadogJSONFormatter().json_record("Hello", {}, record)

    def test_dict_auth(self, rf):
        json_record = self.format_with_auth(rf, {"sid": "session-1", "cid": "client-1"})

        assert json_record["usr.session_id"] == "session-1"
        assert json_record["usr.client_id"] == "client-1"

    def test_mapping_auth(self, rf):
        json_record = self.format_with_auth(rf, JWTCredentialsLike({"sid": "session-1", "cid": "client-1"}))

        assert json_record["usr.session_id"] == "session-1"
        assert json_record["usr.client_id"] == "client-1"
