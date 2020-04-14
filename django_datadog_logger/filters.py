import logging

from django_datadog_logger.celery import get_celery_request
from django_datadog_logger.wsgi import get_wsgi_request


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.celery_request = get_celery_request()
        record.wsgi_request = get_wsgi_request()
        return True
