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
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)  # 👈 add this
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def expire(self):
        """Mark reservation as expired and log it."""
        if self.is_active:
            self.is_active = False
            self.status = 'expired'
            self.save(update_fields=['is_active', 'status'])
            ReservationLog.objects.create(
                reservation=self,
                user=self.user,
                action='expired',
                timestamp=timezone.now()
            )

    def __str__(self):
        return f"{self.user.username} - {self.seat.code} ({self.status})"


class ReservationLog(models.Model):
    """
    Tracks when a reservation was made, cancelled, or expired.
    Remains even if the reservation is deleted.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    reservation = models.ForeignKey(
        'Reservation',
        on_delete=models.SET_NULL,   # 👈 keep the log even if reservation is deleted
        null=True,
        blank=True,
        related_name='logs'
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    seat_code = models.CharField(max_length=50)  # 👈 snapshot of seat at time of log
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.seat_code} - {self.action} by {self.user or 'Unknown'}"
