import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_appointment.settings")

app = Celery("project_appointment")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
