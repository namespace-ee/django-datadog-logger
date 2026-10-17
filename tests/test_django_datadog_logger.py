"""Tests for `django_datadog_logger` package."""

import collections.abc
import logging
from types import SimpleNamespace

from django_datadog_logger.formatters.datadog import DatadogJSONFormatter, get_wsgi_request_auth


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


def test_dict_auth():
    auth = {"sid": "session-1", "cid": "client-1"}
    assert get_wsgi_request_auth(SimpleNamespace(auth=auth)) is auth


def test_mapping_auth():
    auth = JWTCredentialsLike({"sid": "session-1", "cid": "client-1"})
    assert get_wsgi_request_auth(SimpleNamespace(auth=auth)) is auth
