"""Celery application configuration.

Uses Redis as broker and result backend.
Celery beat schedules periodic tasks (critical rides check every 5 min).
"""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "aureavia",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.critical_rides"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    beat_schedule={
        "check-critical-rides": {
            "task": "app.tasks.critical_rides.check_critical_rides_task",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)
