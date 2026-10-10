# This will import the Celery app so that it is always available
# when Django starts, ensuring shared_task decorators work correctly.
from .celery import app as celery_app

__all__ = ('celery_app',)
