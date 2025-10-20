from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Seat(models.Model):
    """
    A seat in the building. The layout is defined by row/col or x/y coordinates.
    You (the admin) will create Seat objects according to the building map.
    """
    code = models.CharField(max_length=20, unique=True)  # e.g., A1, B3
    row = models.CharField(max_length=10, blank=True)
    col = models.CharField(max_length=10, blank=True)
    x = models.IntegerField(null=True, blank=True)  # optional pixel coords
    y = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)  # physically exists/usable
    is_reservable = models.BooleanField(default=True)  # can this seat be booked or not

    def __str__(self):
        return self.code


class Reservation(models.Model):
    """
    Stores when a user books a seat for a specific date.
    Reservation lifespan is limited (e.g., same-day booking window).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='reservations')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (('seat', 'date'),)  # only one reservation per seat per date
        indexes = [models.Index(fields=['date'])]

    def __str__(self):
        return f"{self.date} - {self.seat.code} - {self.user.username}"

    def expire(self):
        """Mark reservation as expired and log the action."""
        self.is_active = False
        self.expires_at = timezone.now()
        self.save(update_fields=['is_active', 'expires_at'])
        ReservationLog.objects.create(
            reservation=self,
            user=self.user,
            action="expired",
            timestamp=self.expires_at
        )


class ReservationLog(models.Model):
    """
    Tracks when a reservation was made or expired.
    Helps with audit/history tracking.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.reservation.seat.code} - {self.action} by {self.user.username}"
