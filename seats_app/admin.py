from django.contrib import admin
from .models import Workspace, Space, Seat, WorkspaceUser, Reservation, ReservationLog


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "created_at", "updated_at")
    search_fields = ("name", "location")


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ("name", "workspace", "is_active", "created_at")
    list_filter = ("workspace", "is_active")
    search_fields = ("name", "workspace__name")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("code", "space", "row", "col", "is_active", "is_reservable")
    list_filter = ("space", "is_active", "is_reservable")
    search_fields = ("code", "space__name")


@admin.register(WorkspaceUser)
class WorkspaceUserAdmin(admin.ModelAdmin):
    list_display = ("user", "workspace", "is_admin")
    list_filter = ("workspace", "is_admin")
    search_fields = ("user__username", "workspace__name")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("user", "workspace", "space", "seat", "date", "status", "is_active")
    list_filter = ("workspace", "space", "status", "is_active", "date")
    search_fields = ("user__username", "seat__code")


@admin.register(ReservationLog)
class ReservationLogAdmin(admin.ModelAdmin):
    list_display = ("seat_code", "action", "user", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("seat_code", "user__username")

admin.site.site_header = "Workspace+ Admin"
admin.site.site_title = "Workspace+ Admin"
admin.site.index_title = "Welcome to Workspace+ Admin"
