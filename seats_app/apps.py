from django.apps import AppConfig
import os

class SeatsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seats_app'

    def ready(self):
        # Prevent multiple threads during development auto-reload
        if os.environ.get("RUN_MAIN") == "true":
            from utils.scheduler import start_daily_scheduler
            start_daily_scheduler(hour=18, minute=0)  # run daily at 6 PM
