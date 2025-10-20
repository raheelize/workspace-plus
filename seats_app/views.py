from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse,HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import time, date,datetime
import json
import pytz
from .models import Seat, Reservation,ReservationLog
from django.contrib import messages

# Time windows
RESERVATION_START = time(hour=9, minute=0)
RESERVATION_END = time(hour=18, minute=0)
BOOKING_OPEN = time(hour=8, minute=30)
BOOKING_CLOSE = time(hour=9, minute=15)

# BOOKING_OPEN = time(hour=23, minute=30)
# BOOKING_CLOSE = time(hour=23, minute=52)

def in_booking_window(now=None):
    """Check if current local time (Asia/Karachi) is within booking window."""
    pk_tz = pytz.timezone('Asia/Karachi')
    now = now or timezone.now()
    local_now = now.astimezone(pk_tz)
    t = local_now.time()

    print("BOOKING_OPEN :", BOOKING_OPEN, "BOOKING_CLOSE :", BOOKING_CLOSE)
    print(BOOKING_OPEN <= t)
    print(t <= BOOKING_CLOSE)
    print(f"[DEBUG] Local time: {local_now}, Time component: {t}")

    if BOOKING_OPEN <= BOOKING_CLOSE:
        # normal case: same day
        return BOOKING_OPEN <= t <= BOOKING_CLOSE
    else:
        # overnight case: e.g., 23:30 → 00:00
        return t >= BOOKING_OPEN or t <= BOOKING_CLOSE


def in_reservation_period(now=None):
    now = now or timezone.localtime()
    t = now.time()
    return RESERVATION_START <= t <= RESERVATION_END



@login_required
def index(request):
    today = date.today()

    # Handle POST booking (when user clicks Book Selected Seat)
    
    seats = list(Seat.objects.filter(is_active=True))

    # Get today’s reservations
    reservations = Reservation.objects.filter(date=today, status = 'active').select_related("seat", "user")

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
    """
    Attempt to book a seat for the current user for today.
    Enforces booking window, one active reservation per user, and audit logs.
    """
    if not in_booking_window():
        return JsonResponse({'ok': False, 'error': 'Booking window is closed.'}, status=403)

    if request.content_type != 'application/json':
        return HttpResponseBadRequest('Expected application/json')

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    seat_id = payload.get('seat_id')
    if not seat_id:
        return JsonResponse({'ok': False, 'error': 'No seat specified.'}, status=400)

    today = date.today()
    expires_at = timezone.make_aware(datetime.combine(today, time(18, 0)))  # auto-expire at 6 PM

    # 🛑 Prevent multiple active reservations per user per day
    if Reservation.objects.filter(user=request.user, date=today, status='active').exists():
        return JsonResponse({'ok': False, 'error': 'You already have an active reservation today.'}, status=403)

    seat = get_object_or_404(Seat, pk=seat_id, is_active=True)

    # 🛑 Ensure seat isn’t already reserved for today (active only)
    if Reservation.objects.filter(seat=seat, date=today, status='active').exists():
        return JsonResponse({'ok': False, 'error': 'Seat already reserved by another user.'}, status=403)

    # ✅ Create new reservation
    reservation = Reservation.objects.create(
        user=request.user,
        seat=seat,
        date=today,
        expires_at=expires_at,
        status='active',
        is_active=True
    )

    # 🪵 Log reservation creation
    ReservationLog.objects.create(
        reservation=reservation,
        user=request.user,
        action='created',
        timestamp=timezone.now()
    )

    return JsonResponse({
        'ok': True,
        'message': f'Seat {seat.code} booked successfully until 6:00 PM.',
        'reservation_id': reservation.id
    })


def cancel_reservation_api(request):
    """Cancel the current user's reservation (soft delete)."""
    if not in_booking_window():
        return JsonResponse({'ok': False, 'error': 'Cannot cancel outside reservation hours'}, status=403)

    today = date.today()
    reservation = Reservation.objects.filter(user=request.user, date=today, is_active=True).first()

    if not reservation:
        return JsonResponse({'ok': False, 'error': 'No active reservation to cancel'}, status=404)

    # 🪵 Log the cancellation
    ReservationLog.objects.create(
        reservation=reservation,
        user=request.user,
        action='cancelled',
        timestamp=timezone.now()
    )

    # 🔄 Mark reservation as cancelled instead of deleting
    reservation.is_active = False
    reservation.status = 'cancelled'   # assuming you have a status field like ('active', 'expired', 'cancelled')
    reservation.save(update_fields=['is_active', 'status'])

    return JsonResponse({'ok': True, 'message': 'Reservation cancelled successfully.'})