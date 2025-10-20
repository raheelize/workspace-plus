from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse,HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import time, date
import json

from .models import Seat, Reservation
from django.contrib import messages

# Time windows
RESERVATION_START = time(hour=9, minute=0)
RESERVATION_END = time(hour=18, minute=0)
BOOKING_OPEN = time(hour=8, minute=30)
BOOKING_CLOSE = time(hour=9, minute=15)


def in_booking_window(now=None):
    now = now or timezone.localtime()
    t = now.time()
    return True
    return BOOKING_OPEN <= t <= BOOKING_CLOSE


def in_reservation_period(now=None):
    now = now or timezone.localtime()
    t = now.time()
    return RESERVATION_START <= t <= RESERVATION_END



@login_required
def index(request):
    today = date.today()

    # Handle POST booking (when user clicks Book Selected Seat)
    if request.method == "POST":
        seat_id = request.POST.get("seat_id")
        if not seat_id:
            messages.error(request, "No seat selected.")
            return redirect("index")

        seat = Seat.objects.get(id=seat_id)

        # Already has a reservation?
        if Reservation.objects.filter(user=request.user, date=today).exists():
            messages.warning(request, "You already have a reservation today.")
            return redirect("index")

        # Seat already booked?
        if Reservation.objects.filter(seat=seat, date=today).exists():
            messages.error(request, "This seat is already reserved.")
            return redirect("index")

        # Booking window check
        if not in_booking_window():
            messages.error(request, "Bookings are only open from 8:30 AM to 9:15 AM.")
            return redirect("index")

        # Create reservation
        Reservation.objects.create(
            user=request.user,
            seat=seat,
            date=today,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        messages.success(request, f"Seat {seat.code} booked successfully!")
        return redirect("index")

    # Get all seats
    seats = list(Seat.objects.filter(is_active=True))

    # Get today’s reservations
    reservations = Reservation.objects.filter(date=today).select_related("seat", "user")

    # Map seat -> reservation
    reservation_map = {res.seat.id: res for res in reservations}

    # Annotate each seat with reservation data
    for seat in seats:
        res = reservation_map.get(seat.id)
        seat.is_reserved = bool(res)
        seat.user = res.user if res else None

    # User’s reservation for today
    user_res = reservations.filter(user=request.user).first()

    context = {
        "today": today,
        "user_reservation": user_res,
        "booking_open": in_booking_window(),
        "reservation_period": in_reservation_period(),
        "seats": seats,
    }

    return render(request, "index.html", context)





@staff_member_required
def admin_map(request):
    """Page to visually position seats by dragging. Staff only."""
    seats = list(Seat.objects.filter(is_active=True))
    # annotate reservation status for visual convenience (optional)
    today = date.today()
    reservations = Reservation.objects.filter(date=today).select_related('seat', 'user')
    rmap = {r.seat.id: r for r in reservations}
    for s in seats:
        res = rmap.get(s.id)
        s.is_reserved = bool(res)
        s.user = res.user if res else None
    return render(request, 'admin_map.html', {'seats': seats})

@require_POST
@staff_member_required
def save_positions(request):
    """Accept JSON: [{id: 1, x: 120, y: 200}, ...] and save to Seat.x/y"""
    if request.content_type != 'application/json':
        return HttpResponseBadRequest('Expected application/json')
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    if not isinstance(payload, list):
        return HttpResponseBadRequest('Expected a list of objects')

    updated = 0
    errors = []
    for item in payload:
        try:
            seat_id = int(item.get('id'))
            x = int(item.get('x'))
            y = int(item.get('y'))
        except Exception as e:
            errors.append(f"Bad item: {item} ({e})")
            continue
        try:
            seat = Seat.objects.get(pk=seat_id)
            seat.x = x
            seat.y = y
            seat.save(update_fields=['x', 'y'])
            updated += 1
        except Seat.DoesNotExist:
            errors.append(f"Seat {seat_id} not found")

    return JsonResponse({'ok': True, 'updated': updated, 'errors': errors})

@login_required
def seat_status_api(request):
    """Return JSON list of seats and their status for today."""
    today = date.today()
    seats = Seat.objects.filter(is_active=True).order_by('code')
    reserved = Reservation.objects.filter(date=today).select_related('seat', 'user')
    seat_map = {r.seat_id: r for r in reserved}

    data = []
    for s in seats:
        r = seat_map.get(s.id)
        status = 'available'
        reserved_by = None
        if r:
            status = 'reserved'
            reserved_by = r.user.username
            if request.user == r.user:
                status = 'mine'
        data.append({
            'id': s.id,
            'code': s.code,
            'row': s.row,
            'col': s.col,
            'x': s.x,
            'y': s.y,
            'status': status,
            'reserved_by': reserved_by,
        })
    return JsonResponse({'seats': data})


@login_required
@require_POST
def book_seat_api(request):
    """Attempt to book a seat for the current user for today.
    Server-side enforces booking window and single-reservation-per-user.
    """
    if not in_booking_window():
        return JsonResponse({'ok': False, 'error': 'Booking window is closed'}, status=403)
    

    if request.content_type != 'application/json':
        return HttpResponseBadRequest('Expected application/json')
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    seat_id = payload.get('seat_id')
    if not seat_id:
        return JsonResponse({'ok': False, 'error': 'No seat specified'}, status=400)

    today = date.today()

    # If user already has a reservation today, forbid another one
    if Reservation.objects.filter(user=request.user, date=today).exists():
        return JsonResponse({'ok': False, 'error': 'You already have a reservation for today'}, status=403)

    seat = get_object_or_404(Seat, pk=seat_id, is_active=True)

    # Make sure seat isn't already reserved for today (race-safe with get_or_create)
    reservation, created = Reservation.objects.get_or_create(user=request.user, seat=seat, date=today)
    if not created:
        return JsonResponse({'ok': False, 'error': 'Seat already reserved'}, status=403)

    return JsonResponse({'ok': True, 'message': 'Seat booked', 'reservation_id': reservation.id})


@login_required
@require_POST
def cancel_reservation_api(request):
    # Allow cancel only inside booking window or before reservation start? Business choice.
    # We'll allow cancellation until reservation end (6:00 PM).
    if not in_reservation_period() and not in_booking_window():
        return JsonResponse({'ok': False, 'error': 'Cannot cancel outside reservation hours'}, status=403)

    today = date.today()
    res = Reservation.objects.filter(user=request.user, date=today).first()
    if not res:
        return JsonResponse({'ok': False, 'error': 'No reservation to cancel'}, status=404)
    res.delete()
    return JsonResponse({'ok': True, 'message': 'Reservation canceled'})