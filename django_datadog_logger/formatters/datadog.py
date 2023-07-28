import datetime
import re
import traceback

import pytz
import json_log_formatter
from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.http.request import split_domain_port
from django.urls import resolve, NoReverseMatch, Resolver404
from rest_framework.compat import unicode_http_header
from rest_framework.exceptions import AuthenticationFailed

from django_datadog_logger.encoders import SafeJsonEncoder
from django_datadog_logger.celery import get_task_name, get_celery_request
import django_datadog_logger.celery
import django_datadog_logger.wsgi

# those fields are excluded from extra dict
# and remains acceptable in record
from django_datadog_logger.recursion import not_recursive, RecursionDetected

EXCLUDE_FROM_EXTRA_ATTRS = {
    "user",
    "auth",
    "username",
    "request_id",
    "client_ip",
    "request",
    "celery_request",
    "wsgi_request",
    "params",
    "sql",
}


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0] or None
    else:
        return request.META.get("REMOTE_ADDR") or None


def determine_version(request):
    if hasattr(request, "version"):
        if request.version is not None:
            return str(request.version)
    elif hasattr(request, "accepted_types"):
        for t in request.accepted_types:
            if t.params.get("version") is not None:
                return unicode_http_header(t.params.get("version"))
    return None


@not_recursive
def get_wsgi_request_auth(wsgi_request):
    try:
        if getattr(wsgi_request, "auth", None) is not None and isinstance(wsgi_request.auth, dict):
            return wsgi_request.auth
    except Exception:  # NOQA
        return None


@not_recursive
def get_wsgi_request_user(wsgi_request):
    if getattr(wsgi_request, "user", None) is not None:
        if getattr(wsgi_request.user, "is_authenticated", False):
            return wsgi_request.user


class DataDogJSONFormatter(json_log_formatter.JSONFormatter):
    def json_record(self, message, extra, record):
        log_entry_dict = {
            "message": message,
            "logger.name": record.name,
            "logger.thread_name": record.threadName,
            "logger.method_name": record.funcName,
            "syslog.timestamp": pytz.utc.localize(datetime.datetime.utcfromtimestamp(record.created)).isoformat(),
            "syslog.severity": record.levelname,
        }

        # Add special `dd.` log record attributes added by `ddtrace` library
        # For example: dd.trace_id, dd.span_id, dd.service, dd.env, dd.version, etc
        log_entry_dict.update(self.get_datadog_attributes(record))

        wsgi_request = self.get_wsgi_request()
        if wsgi_request is not None:
            log_entry_dict["network.client.ip"] = get_client_ip(wsgi_request)

            try:
                domain, port = split_domain_port(wsgi_request.get_host())
            except DisallowedHost:
                domain, port = None, None

            try:
                resolver_match = resolve(wsgi_request.path)
            except (NoReverseMatch, Resolver404):
                resolver_match = None

            log_entry_dict["http.url"] = wsgi_request.get_full_path()
            log_entry_dict["http.url_details.host"] = domain
            log_entry_dict["http.url_details.port"] = int(port) if port else None
            log_entry_dict["http.url_details.path"] = wsgi_request.path_info
            log_entry_dict["http.url_details.queryString"] = wsgi_request.GET.dict()
            log_entry_dict["http.url_details.scheme"] = wsgi_request.scheme
            log_entry_dict["http.url_details.view_name"] = resolver_match.view_name if resolver_match else None
            log_entry_dict["http.method"] = wsgi_request.method
            log_entry_dict["http.accept"] = wsgi_request.META.get("HTTP_ACCEPT")
            log_entry_dict["http.referer"] = wsgi_request.META.get("HTTP_REFERER")
            log_entry_dict["http.useragent"] = wsgi_request.META.get("HTTP_USER_AGENT")
            log_entry_dict["http.request_version"] = determine_version(wsgi_request)

            if hasattr(wsgi_request, "request_id"):
                log_entry_dict["http.request_id"] = wsgi_request.request_id

            try:
                auth = get_wsgi_request_auth(wsgi_request)
            except RecursionDetected:
                auth = None

            if auth:
                if "sid" in auth:
                    log_entry_dict["usr.session_id"] = auth["sid"]
                if "cid" in auth:
                    log_entry_dict["usr.client_id"] = auth["cid"]

            try:
                user = get_wsgi_request_user(wsgi_request)
            except RecursionDetected:
                user = None

            if user:
                log_entry_dict["usr.id"] = getattr(user, "pk", None)
                log_entry_dict["usr.name"] = getattr(user, getattr(user, "USERNAME_FIELD", "username"), None)
                log_entry_dict["usr.email"] = getattr(user, "email", None)

            if getattr(wsgi_request, "session", None) is not None and getattr(wsgi_request.session, "session_key"):
                log_entry_dict["usr.session_key"] = wsgi_request.session.session_key

        if hasattr(settings, "DATADOG_TRACE") and "TAGS" in settings.DATADOG_TRACE:
            log_entry_dict["syslog.env"] = settings.DATADOG_TRACE["TAGS"].get("env")

        if record.exc_info:
            if hasattr(record, "status_code"):
                log_entry_dict["error.kind"] = record.status_code
                log_entry_dict["error.message"] = record.msg
            else:
                log_entry_dict["error.kind"] = record.exc_info[0].__name__
                for msg in traceback.format_exception_only(record.exc_info[0], record.exc_info[1]):
                    log_entry_dict["error.message"] = msg.strip()
            log_entry_dict["error.stack"] = self.formatException(record.exc_info)

        if hasattr(record, "duration"):
            log_entry_dict["duration"] = record.duration

        if hasattr(record, "sql"):
            log_entry_dict["db.statement"] = record.sql

        celery_request = get_celery_request()
        if celery_request is not None:
            log_entry_dict["celery.request_id"] = celery_request.id
            log_entry_dict["celery.task_name"] = get_task_name(celery_request)
        elif record.name in {"celery.app.trace", "celery.worker.strategy"} and "data" in extra:
            if "id" in extra["data"]:
                log_entry_dict["celery.request_id"] = extra["data"]["id"]
            if "name" in extra["data"]:
                log_entry_dict["celery.task_name"] = extra["data"]["name"]
            if "runtime" in extra["data"]:
                log_entry_dict["duration"] = extra["data"]["runtime"] * 1000000000

        if hasattr(settings, "DJANGO_DATADOG_LOGGER_EXTRA_INCLUDE"):
            if re.match(getattr(settings, "DJANGO_DATADOG_LOGGER_EXTRA_INCLUDE"), record.name):
                log_entry_dict.update(extra)

        return log_entry_dict

    def get_datadog_attributes(self, record):
        """Helper to extract dd.* attributes from the log record."""
        return {attr_name: record.__dict__[attr_name] for attr_name in record.__dict__ if attr_name.startswith("dd.")}

    def get_wsgi_request(self):
        return django_datadog_logger.wsgi.get_wsgi_request()

    def to_json(self, record):
        return self.json_lib.dumps(record, cls=SafeJsonEncoder)

    def extra_from_record(self, record):
        """Returns `extra` dict you passed to logger.

        The `extra` keyword argument is used to populate the `__dict__` of
        the `LogRecord`.

        """
        return {
            attr_name: record.__dict__[attr_name]
            for attr_name in record.__dict__
            if attr_name not in json_log_formatter.BUILTIN_ATTRS.union(EXCLUDE_FROM_EXTRA_ATTRS)
        }
