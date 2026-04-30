"""Celery app for async notifications and periodic tasks."""

import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://:allo_redis_pass@redis:6379/0")

app = Celery("allo", broker=f"{REDIS_URL}/1", backend=f"{REDIS_URL}/2")
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
)

app.conf.beat_schedule = {
    "send_day_reminders": {
        "task": "src.tasks.send_reminders",
        "schedule": crontab(hour=9, minute=0),
        "kwargs": {"type": "day_before"},
    },
    "send_hour_reminders": {
        "task": "src.tasks.send_reminders",
        "schedule": crontab(minute="*/15"),
        "kwargs": {"type": "hour_before"},
    },
    "cleanup_old_sessions": {
        "task": "src.tasks.cleanup_sessions",
        "schedule": crontab(hour=4, minute=0),
    },
}

# Import tasks to register them
import src.tasks  # noqa: F401
