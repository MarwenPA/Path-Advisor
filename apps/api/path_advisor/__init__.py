"""Package init — Celery/Django wiring (canonical two lines).

Story 8.1 discovery: this file was EMPTY, so the configured Celery app
(`path_advisor.celery`, redis broker + `CELERY_*` settings, including
`CELERY_TASK_ALWAYS_EAGER` in tests) was only ever imported by the worker
entrypoint. Everywhere else — runserver, gunicorn, pytest — `shared_task`
bound to Celery's DEFAULT app: `.delay()` published to amqp://127.0.0.1:5672
(nothing listens there) and test eager-mode silently never applied; existing
tests only pass because they patch `.delay` or call tasks synchronously.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
