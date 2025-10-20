import threading
import time
from datetime import datetime, timedelta
from django.core.management import call_command

def start_daily_scheduler(hour=18, minute=0):
    """
    Run 'expire_reservation' every day at hour:minute (default 18:00 PKT).
    """
    def run_loop():
        while True:
            now = datetime.now()
            # Compute next run datetime
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            sleep_seconds = (next_run - now).total_seconds()
            print(f"[Scheduler] Next expire_reservations run at: {next_run}")
            time.sleep(sleep_seconds)

            try:
                print(f"[{datetime.now()}] Running expire_reservations...")
                call_command("expire_reservations")
            except Exception as e:
                print(f"[Scheduler Error] {e}")

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
