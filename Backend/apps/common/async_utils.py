import logging

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


def dispatch_background_task(task, *, defer: bool = True, run_kwargs: dict | None = None, async_kwargs: dict | None = None) -> None:
    run_kwargs = run_kwargs or {}
    async_kwargs = async_kwargs or run_kwargs

    def runner():
        if getattr(settings, 'ENABLE_ASYNC_TASKS', False):
            task.delay(**async_kwargs)
            return

        try:
            task.run(**run_kwargs)
        except Exception as exc:  # pragma: no cover
            logger.warning('Could not execute background task %s: %s', getattr(task, 'name', repr(task)), exc)

    connection = transaction.get_connection()
    if defer and connection.in_atomic_block:
        transaction.on_commit(runner)
        return
    runner()
