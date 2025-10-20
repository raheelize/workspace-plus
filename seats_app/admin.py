from django.contrib import admin
from .models import Seat, Reservation,ReservationLog

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('code', 'row', 'col', 'x', 'y', 'is_active')
    search_fields = ('code',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'seat', 'date', 'status', 'is_active', 'expires_at')
    list_filter = ('status', 'date', 'is_active')


@admin.register(ReservationLog)
class ReservationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__username', 'seat__code')


admin.site.site_header = "Workspace+ Admin"
admin.site.site_title = "Workspace+ Admin"
admin.site.index_title = "Welcome to Workspace+ Admin"
