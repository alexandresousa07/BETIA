from celery import Celery
from celery.schedules import crontab

from app.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "football_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "sync-live-matches": {
        "task": "app.workers.tasks.sync_live_matches",
        "schedule": 60.0,
    },
    "update-monitored-matches": {
        "task": "app.workers.tasks.update_monitored_matches",
        "schedule": 30.0,
    },
    "match-odds": {
        "task": "app.workers.tasks.match_odds",
        "schedule": 120.0,
    },
    "sync-leagues-daily": {
        "task": "app.workers.tasks.sync_leagues",
        "schedule": crontab(hour=2, minute=0),
    },
    "train-models-weekly": {
        "task": "app.workers.tasks.train_historical_models",
        "schedule": crontab(hour=3, minute=0, day_of_week=1),
    },
}

celery_app.autodiscover_tasks(["app.workers"])
