# management/commands/expire_reservations.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from seats_app.models import Reservation

class Command(BaseCommand):
    help = "Expire reservations that are past their expiry time"

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Reservation.objects.filter(is_active=True, expires_at__lte=now)
        for res in expired:
            res.expire()
        self.stdout.write(self.style.SUCCESS(f"Expired {expired.count()} reservations."))
