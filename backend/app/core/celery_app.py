"""
Celery application configuration.

Workers import this module to register tasks.
"""

from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "leopard",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
    include=[
        "app.workers.vrp_worker",
        "app.workers.eta_worker",
        "app.workers.gps_archiver",
        "app.workers.notification_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)
