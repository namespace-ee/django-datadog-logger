"""Tests for `django_datadog_logger` package."""

import logging

from django_datadog_logger.formatters.datadog import DatadogJSONFormatter


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
