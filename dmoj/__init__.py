import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dmoj.settings")

from dmoj.celery import app as celery_app
