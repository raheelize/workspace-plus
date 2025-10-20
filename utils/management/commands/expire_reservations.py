from django.core.management.base import BaseCommand
from django.utils import timezone
from seats_app.models import Reservation, ReservationLog
import pytz


class Command(BaseCommand):
    help = "Expire all reservations that are past their expiry time and log the action."

    def handle(self, *args, **options):

        pk_tz = pytz.timezone('Asia/Karachi')

        # naive DB field assumed to be PK time
        local_now = timezone.localtime(timezone.now(), pk_tz)
        expired_reservations = Reservation.objects.filter(is_active=True, expires_at__lte=local_now)
        print(local_now)
        print(expired_reservations)


        total_expired = expired_reservations.count()

        if not total_expired:
            self.stdout.write(self.style.WARNING("No expired reservations found."))
            return

        for reservation in expired_reservations:
            # Update reservation status
            reservation.is_active = False
            reservation.save(update_fields=["is_active"])

            # Log expiration event
            ReservationLog.objects.create(
                reservation=reservation,
                action="expired",
                timestamp=timezone.now()
            )

        self.stdout.write(
            self.style.SUCCESS(f"✅ Successfully expired and logged {total_expired} reservations.")
        )

