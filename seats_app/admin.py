from django.contrib import admin
from .models import Seat, Reservation

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('code', 'row', 'col', 'x', 'y', 'is_active')
    search_fields = ('code',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('date', 'seat', 'user', 'created_at')
    list_filter = ('date',)
    search_fields = ('user__username', 'seat__code')




admin.site.site_header = "Workplace+ Admin"
admin.site.site_title = "Workplace+ Admin"
admin.site.index_title = "Welcome to Workplace+ Admin"
