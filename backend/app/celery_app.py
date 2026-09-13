"""Configuration Celery pour les tâches en arrière-plan."""
from celery import Celery
from celery.schedules import crontab
import os

celery_app = Celery(
    'brvm_tasks',
    broker=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://redis:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Abidjan',
    enable_utc=True,
    beat_schedule={
        'scrape-news-every-2-hours': {
            'task': 'app.tasks.scrape_news_task',
            'schedule': 7200.0,  # 2 heures en secondes
        },
        'update-brvm-daily': {
            'task': 'app.tasks.update_brvm_daily_task',
            'schedule': crontab(hour=18, minute=0),  # Tous les jours à 18h00
        }
    }
)
