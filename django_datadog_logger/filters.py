import logging

from django_datadog_logger.request import get_request


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request = get_request()
        return True
