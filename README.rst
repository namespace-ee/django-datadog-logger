=====================
Django DataDog Logger
=====================


.. image:: https://img.shields.io/pypi/v/django-datadog-logger.svg
        :target: https://pypi.python.org/pypi/django-datadog-logger

.. image:: https://img.shields.io/travis/namespace-ee/django-datadog-logger.svg
        :target: https://travis-ci.com/namespace-ee/django-datadog-logger

.. image:: https://readthedocs.org/projects/django-datadog-logger/badge/?version=latest
        :target: https://django-datadog-logger.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/namespace-ee/django-datadog-logger/shield.svg
     :target: https://pyup.io/repos/github/namespace-ee/django-datadog-logger/
     :alt: Updates



Django DataDog Logger integration package.


* Free software: MIT license
* Documentation: https://django-datadog-logger.readthedocs.io.


Quick start
-----------

Set up request id tracking (in front) and logging middlewares (at the end):

.. code-block:: python

    MIDDLEWARE = [
        "django_datadog_logger.middleware.request_id.RequestIdMiddleware",
        # ...
        "django_datadog_logger.middleware.error_log.ErrorLoggingMiddleware",
        "django_datadog_logger.middleware.request_log.RequestLoggingMiddleware",
    ]

Configure LOGGERS in your Django settings file:

.. code-block:: python

    API_LOG_ROOT = env.str("API_LOG_ROOT")
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {"format": "{levelname} {message}", "style": "{"},
            "json": {"()": "django_datadog_logger.formatters.datadog.DataDogJSONFormatter"},
        },
        "handlers": {
            "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "console"},
            "application": {
                "level": API_LOG_APPLICATION_LEVEL,
                "class": "logging.FileHandler",
                "filename": os.path.join(API_LOG_ROOT, "api.application.log"),
                "formatter": "json",
            },
            "state": {
                "level": API_LOG_STATE_LEVEL,
                "class": "logging.FileHandler",
                "filename": os.path.join(API_LOG_ROOT, "api.state.log"),
                "formatter": "json",
            },
            "request": {
                "level": API_LOG_REQUEST_LEVEL,
                "class": "logging.FileHandler",
                "filename": os.path.join(API_LOG_ROOT, "api.request.log"),
                "formatter": "json",
            },
            "session": {
                "level": API_LOG_SESSION_LEVEL,
                "class": "logging.FileHandler",
                "filename": os.path.join(API_LOG_ROOT, "api.session.log"),
                "formatter": "json",
            },
            "error": {
                "level": API_LOG_ERROR_LEVEL,
                "class": "logging.FileHandler",
                "filename": os.path.join(API_LOG_ROOT, "api.error.log"),
                "formatter": "json",
            },
        },
        "loggers": {
            "": {"handlers": ["console", "error"], "level": "DEBUG", "propagate": True},
            "ddtrace": {"handlers": ["error"], "level": "ERROR", "propagate": False},
            "django.db.backends": {"handlers": ["error"], "level": "ERROR", "propagate": False},
            "twilio": {"handlers": ["error"], "level": "ERROR", "propagate": False},
            "my_project": {"handlers": ["application"], "level": "INFO", "propagate": False},
            "my_project.throttling": {"handlers": ["application"], "level": "DEBUG", "propagate": False},
            "my_project.vehicles.viewsets.state": {"handlers": ["state"], "level": "INFO", "propagate": False},
            "my_project.accounts.session": {"handlers": ["session"], "level": "DEBUG", "propagate": False},
            "my_project.session": {"handlers": ["session"], "level": "DEBUG", "propagate": False},
            "django_auth_ldap": {"level": "DEBUG", "handlers": ["session"], "propagate": False},
            "django_datadog_logger.middleware.error_log": {"handlers": ["error"], "level": "INFO", "propagate": False},
            "django_datadog_logger.middleware.request_log": {"handlers": ["request"], "level": "INFO", "propagate": False},
            "django_datadog_logger.rest_framework": {"handlers": ["application"], "level": "INFO", "propagate": False},
        },
    }
    DJANGO_DATADOG_LOGGER_EXTRA_INCLUDE = r"^(django_datadog_logger|my_project)(|\..+)$"

Add Celery logger configuration and request_id tracking decorator to tasks:

.. code-block:: python

    import logging

    from celery import Celery, shared_task
    from celery.result import AsyncResult
    from celery.signals import after_setup_logger, after_setup_task_logger
    from django.conf import settings
    from django_datadog_logger.celery import store_celery_request

    logger = logging.getLogger(__name__)


    @after_setup_logger.connect
    def on_after_setup_logger(logger, *args, **kwargs):
        from django_datadog_logger.formatters.datadog import DataDogJSONFormatter

        if settings.API_LOG_CELERY_JSON:
            formatter = DataDogJSONFormatter()
            for handler in list(logger.handlers):
                handler.setFormatter(formatter)
                handler.setLevel(settings.API_LOG_CELERY_LEVEL)


    @after_setup_task_logger.connect
    def on_after_setup_task_logger(logger, *args, **kwargs):
        from django_datadog_logger.formatters.datadog import DataDogJSONFormatter

        if settings.API_LOG_CELERY_JSON:
            formatter = DataDogJSONFormatter()
            for handler in list(logger.handlers):
                handler.setFormatter(formatter)
                handler.setLevel(settings.API_LOG_CELERY_LEVEL)


    app = Celery("my_project")

    # Using a string here means the worker will not have to
    # pickle the object when using Windows.
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


    @shared_task(bind=True)
    @store_celery_request
    def debug_task(self):
        print("Request: {0!r}".format(self.request))
        logger.critical("CRITICAL", extra={"level": "CRITICAL"})
        logger.error("ERROR", extra={"level": "ERROR"})
        logger.warning("WARNING", extra={"level": "WARNING"})
        logger.info("INFO", extra={"level": "INFO"})
        logger.debug("DEBUG", extra={"level": "DEBUG"})
        return 42
        
ddtrace
-------

The ddtrace library has an option to inject tracing context data into log records: https://ddtrace.readthedocs.io/en/stable/advanced_usage.html#logs-injection

There is a helper to look for those attributes and add them automatically to the log entry created by this library.

.. code-block:: python

    # log.py

    # Patch logging library to inject dd.* attributes on log records
    import ddtrace
    ddtrace.patch(logging=True)

    # Configure logger with DataDogJSONFormatter
    import logging
    from django_datadog_logger.formatters.datadog import DataDogJSONFormatter

    logger = logging.root

    handler = logging.StreamHandler()
    handler.formatter = DataDogJSONFormatter()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


    # Log a test message
    logger.info("test")

.. code-block:: bash

    $ DD_SERVICE=django DD_ENV=test DD_VERSION=1234 python log.py
    {"message": "test", "logger.name": "root", "logger.thread_name": "MainThread", "logger.method_name": "<module>", "syslog.timestamp": "2021-08-23T18:26:10.391099+00:00", "syslog.severity": "INFO", "dd.version": "1234", "dd.env": "test", "dd.service": "django", "dd.trace_id": "0", "dd.span_id": "0"}

If you remove the call to `datadog.patch(logging=True)` you end up with:

.. code-block:: bash

    $ python test.py
    {"message": "test", "logger.name": "root", "logger.thread_name": "MainThread", "logger.method_name": "<module>", "syslog.timestamp": "2021-08-23T18:27:47.951461+00:00", "syslog.severity": "INFO"}


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
