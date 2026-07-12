from celery import Celery
from celery.schedules import crontab


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    celery.conf.beat_schedule = {
        "daily-deadline-reminders": {
            "task": "tasks.send_deadline_reminders",
            "schedule": crontab(hour=9, minute=0),
        },
        "monthly-activity-report": {
            "task": "tasks.send_monthly_report",
            "schedule": crontab(day_of_month=1, hour=8, minute=0),
        },
    }
    celery.conf.timezone = "Asia/Kolkata"

    return celery
