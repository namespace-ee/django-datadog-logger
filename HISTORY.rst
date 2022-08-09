=======
History
=======

0.5.1 (2022-08-09)
------------------

* Fixed: ActionLoginMixin class methods `perform_create` and `perform_update` call `super()`. Remove atomic transaction

0.5.0 (2021-10-20)
------------------

* Added support for Celery v5+

0.4.0 (2021-08-27)
------------------

* Enhancement: Updated formatting in README.rst #5
* Enhancement: Extract and add dd.* attributes from log record to log entry dict #6
* Fixed: KeyError because a dict appears where a list is expected #7

0.3.5 (2021-06-14)
------------------

* Prevent recursion when warnings are logged whilst accessing WSGI request.user

0.3.4 (2021-06-14)
------------------

* Fixed import error for future package

0.3.3 (2020-11-04)
------------------

* Added support for incoming HTTP X-Request-ID header values

0.3.2 (2020-04-24)
------------------

* Respect User.USERNAME_FIELD

0.3.1 (2020-04-24)
------------------

* Removed API_LOG_REQUEST_DURATION_WARN_SECONDS

0.3.0 (2020-04-15)
------------------

* Improved Celery task received messages logging.
* Removed RequestIdFilter (not needed anymore).

0.2.0 (2020-04-14)
------------------

* Added Celery request local.

0.1.0 (2020-02-17)
------------------

* First release on PyPI.
