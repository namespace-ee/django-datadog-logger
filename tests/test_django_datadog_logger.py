"""Tests for `django_datadog_logger` package."""
import logging
import unittest

from django.conf import settings

from django_datadog_logger.formatters.datadog import DataDogJSONFormatter


class DjangoDatadogLoggerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not settings.configured:
            settings.configure()

    def test_format_json_accepts_a_tuple_of_nones_as_exc_info(self):
        """
        When logger is called with exc_info=True, then the exc_info
        attribute of the LogRecord is a tuple of (None, None, None).
        """
        record = logging.LogRecord(
            'foo',
            logging.ERROR,
            'foo.py',
            42,
            'This is an error',
            None,
            (None, None, None)
        )
        formatter = DataDogJSONFormatter()
        json_record = formatter.json_record('Foo', {}, record)

        self.assertEqual(json_record.get('error.kind'), None)
