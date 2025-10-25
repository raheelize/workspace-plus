from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Workspace(models.Model):
    """Represents a workspace (e.g., a building or office floor)"""

    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Space(models.Model):
    """Represents a specific space/area inside a workspace"""

    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="spaces"
    )
    name = models.CharField(max_length=255)
    width = models.FloatField(help_text="Width of the space")
    height = models.FloatField(help_text="Height of the space")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("workspace", "name")

    def __str__(self):
        return f"{self.workspace.name} - {self.name}"


class Seat(models.Model):
    """A seat in a specific space inside a workspace"""

    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="seats")
    code = models.CharField(max_length=20)
    row = models.CharField(max_length=10, blank=True)
    col = models.CharField(max_length=10, blank=True)
    x = models.IntegerField(null=True, blank=True)
    y = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_reservable = models.BooleanField(default=True)

    class Meta:
        unique_together = ("space", "code")

    def __str__(self):
        return f"{self.space.name} - {self.code}"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    def expire(self):
        """Mark reservation as expired and log it."""
        if self.is_active:
            self.is_active = False
            self.status = "expired"
            self.save(update_fields=["is_active", "status"])
            ReservationLog.objects.create(
                reservation=self,
                user=self.user,
                seat_code=self.seat.code,
                action="expired",
                timestamp=timezone.now(),
            )

    def __str__(self):
        return f"{self.user.username} - {self.seat.code} ({self.status})"


class ReservationLog(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    reservation = models.ForeignKey(
        "Reservation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    seat_code = models.CharField(max_length=50)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.seat_code} - {self.action} by {self.user or 'Unknown'}"


class WorkspaceUser(models.Model):
    """
    Tracks which users are assigned to which workspaces.
    Also indicates workspace-level admin rights.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="workspace_assignments"
    )
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="assigned_users"
    )
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "workspace")

    def __str__(self):
        return f"{self.user.username} - {self.workspace.name} ({'Admin' if self.is_admin else 'User'})"
