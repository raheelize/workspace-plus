from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_POST
from datetime import time, date, datetime
import json
import pytz
from .models import Workspace, Space, Seat, Reservation, ReservationLog, WorkspaceUser
from django.contrib import messages

# ----------------------------
# Time Windows
# ----------------------------
RESERVATION_START = time(hour=9, minute=0)
RESERVATION_END = time(hour=18, minute=0)
BOOKING_OPEN = time(hour=8, minute=30)
BOOKING_CLOSE = time(hour=9, minute=15)

# ----------------------------
# Utility Functions
# ----------------------------
def in_booking_window(now=None):
    pk_tz = pytz.timezone('Asia/Karachi')
    now = now or timezone.now()
    local_now = now.astimezone(pk_tz)
    t = local_now.time()
    if BOOKING_OPEN <= BOOKING_CLOSE:
        return BOOKING_OPEN <= t <= BOOKING_CLOSE
    else:
        return t >= BOOKING_OPEN or t <= BOOKING_CLOSE

def in_reservation_period(now=None):
    now = now or timezone.localtime()
    t = now.time()
    return RESERVATION_START <= t <= RESERVATION_END

def get_user_workspaces(user):
    return Workspace.objects.filter(assigned_users__user=user).distinct()

def get_user_is_admin(user, workspace):
    return WorkspaceUser.objects.filter(user=user, workspace=workspace, is_admin=True).exists()

# ----------------------------
# Frontend Views
# ----------------------------
def index(request):
    return render(request, "index.html")

@login_required
def workspace(request):
    today = date.today()
    workspaces = get_user_workspaces(request.user)
    selected_workspace_id = request.GET.get('workspace')
    workspace = workspaces.filter(id=selected_workspace_id).first() if selected_workspace_id else workspaces.first()

    if not workspace:
        return render(request, "workspace.html", {"error": "You are not assigned to any workspace."})

    spaces = workspace.spaces.filter(is_active=True).order_by('id')
    selected_space_id = request.GET.get('space')
    space = spaces.filter(id=selected_space_id).first() if selected_space_id else spaces.first()
    seats = space.seats.filter(is_active=True).order_by('code') if space else []

    reservations = Reservation.objects.filter(date=today, status='active', workspace=workspace, space=space).select_related("seat", "user")
    reservation_map = {res.seat.id: res for res in reservations}

    for seat in seats:
        res = reservation_map.get(seat.id)
        seat.is_reserved = bool(res)
        seat.user = res.user if res else None

    user_res = reservations.filter(user=request.user).first()

    context = {
        "today": today,
        "workspaces": workspaces,
        "workspace": workspace,
        "spaces": spaces,
        "space": space,
        "user_reservation": user_res,
        "booking_open": in_booking_window(),
        "reservation_period": in_reservation_period(),
        "seats": seats,
    }
    return render(request, "workspace.html", context)

# ----------------------------
# Admin CRUD Views (AJAX/Modal)
# ----------------------------
@login_required
def admin_workspace_crud(request, pk=None):
    """Handles create/edit/delete Workspace"""
    if not request.user.is_superuser:
        return JsonResponse({"ok": False, "error": "Unauthorized"}, status=403)

    if request.method == "POST":
        action = request.POST.get("action")
        name = request.POST.get("name", "").strip()
        location = request.POST.get("location", "").strip()

        try:
            if action == "create":
                if not name:
                    return JsonResponse({"ok": False, "error": "Workspace name is required."})
                with transaction.atomic():
                    ws = Workspace.objects.create(name=name, location=location)
                return JsonResponse({"ok": True, "id": ws.id, "name": ws.name})

            elif action == "edit" and pk:
                ws = get_object_or_404(Workspace, pk=pk)
                ws.name = name or ws.name
                ws.location = location or ws.location
                with transaction.atomic():
                    ws.save()
                return JsonResponse({"ok": True, "id": ws.id, "name": ws.name})

            elif action == "delete" and pk:
                ws = get_object_or_404(Workspace, pk=pk)
                ws.delete()
                return JsonResponse({"ok": True})

            else:
                return JsonResponse({"ok": False, "error": "Invalid action."})

        except IntegrityError:
            return JsonResponse({"ok": False, "error": "Duplicate workspace name. Please choose another."})
        except Exception as e:
            return JsonResponse({"ok": False, "error": f"Unexpected error: {str(e)}"})

    # GET → modal HTML
    try:
        if pk:
            ws = get_object_or_404(Workspace, pk=pk)
            html = f'''
                <h2 class="text-lg font-semibold mb-2">Edit Workspace</h2>
                <input type="text" id="workspace-name" class="border px-2 py-1 w-full mb-2" value="{ws.name}">
                <input type="text" id="workspace-location" class="border px-2 py-1 w-full mb-2" value="{ws.location}">
                <button class="bg-yellow-500 text-white px-3 py-1 rounded" onclick="submitWorkspace('edit',{ws.id})">Save</button>
                <button class="bg-red-600 text-white px-3 py-1 rounded" onclick="submitWorkspace('delete',{ws.id})">Delete</button>
            '''
        else:
            html = '''
                <h2 class="text-lg font-semibold mb-2">Create Workspace</h2>
                <input type="text" id="workspace-name" class="border px-2 py-1 w-full mb-2" placeholder="Workspace Name">
                <input type="text" id="workspace-location" class="border px-2 py-1 w-full mb-2" placeholder="Location">
                <button class="bg-blue-600 text-white px-3 py-1 rounded" onclick="submitWorkspace('create')">Create</button>
            '''
        return JsonResponse({"ok": True, "html": html})
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Unexpected error: {str(e)}"})


@login_required
def admin_space_crud(request, workspace_id=None, pk=None):
    """Handles create/edit/delete Space"""
    workspace = get_object_or_404(Workspace, pk=workspace_id) if workspace_id else None
    if not (request.user.is_superuser or (workspace and get_user_is_admin(request.user, workspace))):
        return JsonResponse({"ok": False, "error": "Unauthorized"}, status=403)

    if request.method == "POST":
        action = request.POST.get("action")
        name = request.POST.get("name", "").strip()
        width = request.POST.get("width")
        height = request.POST.get("height")

        try:
            if action == "create":
                if not all([name, width, height]):
                    return JsonResponse({"ok": False, "error": "All fields are required."})
                with transaction.atomic():
                    sp = Space.objects.create(
                        workspace=workspace,
                        name=name,
                        width=float(width),
                        height=float(height)
                    )
                return JsonResponse({"ok": True, "id": sp.id, "name": sp.name})

            elif action == "edit" and pk:
                sp = get_object_or_404(Space, pk=pk)
                sp.name = name or sp.name
                sp.width = float(width or sp.width)
                sp.height = float(height or sp.height)
                with transaction.atomic():
                    sp.save()
                return JsonResponse({"ok": True, "id": sp.id, "name": sp.name})

            elif action == "delete" and pk:
                sp = get_object_or_404(Space, pk=pk)
                sp.delete()
                return JsonResponse({"ok": True})

            else:
                return JsonResponse({"ok": False, "error": "Invalid action."})

        except IntegrityError:
            return JsonResponse({"ok": False, "error": "Duplicate space name in this workspace."})
        except ValueError:
            return JsonResponse({"ok": False, "error": "Invalid numeric values for width or height."})
        except Exception as e:
            return JsonResponse({"ok": False, "error": f"Unexpected error: {str(e)}"})

    # GET → modal HTML
    try:
        if pk:
            sp = get_object_or_404(Space, pk=pk)
            html = f'''
                <h2 class="text-lg font-semibold mb-2">Edit Space</h2>
                <input type="text" id="space-name" class="border px-2 py-1 w-full mb-2" value="{sp.name}">
                <input type="number" id="space-width" class="border px-2 py-1 w-full mb-2" value="{sp.width}">
                <input type="number" id="space-height" class="border px-2 py-1 w-full mb-2" value="{sp.height}">
                <button class="bg-yellow-500 text-white px-3 py-1 rounded" onclick="submitSpace('edit',{sp.id})">Save</button>
                <button class="bg-red-600 text-white px-3 py-1 rounded" onclick="submitSpace('delete',{sp.id})">Delete</button>
            '''
        else:
            html = '''
                <h2 class="text-lg font-semibold mb-2">Create Space</h2>
                <input type="text" id="space-name" class="border px-2 py-1 w-full mb-2" placeholder="Space Name">
                <input type="number" id="space-width" class="border px-2 py-1 w-full mb-2" placeholder="Width">
                <input type="number" id="space-height" class="border px-2 py-1 w-full mb-2" placeholder="Height">
                <button class="bg-blue-600 text-white px-3 py-1 rounded" onclick="submitSpace('create')">Create</button>
            '''
        return JsonResponse({"ok": True, "html": html})
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Unexpected error: {str(e)}"})

@login_required
def admin_seat_crud(request, space_id=None, pk=None):
    """Handles create/edit/delete Seat"""
    space = get_object_or_404(Space, pk=space_id) if space_id else None
    if not (request.user.is_superuser or (space and get_user_is_admin(request.user, space.workspace))):
        return JsonResponse({"ok": False, "error": "Unauthorized"}, status=403)

    if request.method == "POST":
        action = request.POST.get("action")
        code = request.POST.get("code", "").strip()
        row = request.POST.get("row", "").strip()
        col = request.POST.get("col", "").strip()

        try:
            if action == "create":
                if not code:
                    return JsonResponse({"ok": False, "error": "Seat code is required."})
                with transaction.atomic():
                    st = Seat.objects.create(space=space, code=code, row=row, col=col)
                return JsonResponse({"ok": True, "id": st.id, "code": st.code})

            elif action == "edit" and pk:
                st = get_object_or_404(Seat, pk=pk)
                st.code = code or st.code
                st.row = row or st.row
                st.col = col or st.col
                with transaction.atomic():
                    st.save()
                return JsonResponse({"ok": True, "id": st.id, "code": st.code})

            elif action == "delete" and pk:
                st = get_object_or_404(Seat, pk=pk)
                st.delete()
                return JsonResponse({"ok": True})

            else:
                return JsonResponse({"ok": False, "error": "Invalid action."})

        except IntegrityError as e:
            return JsonResponse({"ok": False, "error": "Duplicate seat code in this space."})
        except Exception as e:
            return JsonResponse({"ok": False, "error": f"Unexpected error: {str(e)}"})

    # GET → modal HTML
    try:
        if pk:
            st = get_object_or_404(Seat, pk=pk)
            html = f'''
                <h2 class="text-lg font-semibold mb-2">Edit Seat</h2>
                <input type="text" id="seat-code" class="border px-2 py-1 w-full mb-2" value="{st.code}">
                <input type="text" id="seat-row" class="border px-2 py-1 w-full mb-2" value="{st.row}">
                <input type="text" id="seat-col" class="border px-2 py-1 w-full mb-2" value="{st.col}">
                <button class="bg-yellow-500 text-white px-3 py-1 rounded" onclick="submitSeat('edit',{st.id})">Save</button>
                <button class="bg-red-600 text-white px-3 py-1 rounded" onclick="submitSeat('delete',{st.id})">Delete</button>
            '''
        else:
            html = '''
                <h2 class="text-lg font-semibold mb-2">Create Seat</h2>
                <input type="text" id="seat-code" class="border px-2 py-1 w-full mb-2" placeholder="Seat Code">
                <input type="text" id="seat-row" class="border px-2 py-1 w-full mb-2" placeholder="Row">
                <input type="text" id="seat-col" class="border px-2 py-1 w-full mb-2" placeholder="Column">
                <button class="bg-blue-600 text-white px-3 py-1 rounded" onclick="submitSeat('create')">Create</button>
            '''
        return JsonResponse({"ok": True, "html": html})

    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Unexpected error: {str(e)}"})

# ----------------------------
# Admin Map & Seat Positioning
# ----------------------------
@login_required
def admin_map(request):
    workspace_id = request.GET.get("workspace")
    space_id = request.GET.get("space")

    print(workspace_id)

    # 🔹 Get allowed workspaces for user
    workspaces = (
        Workspace.objects.all()
        if request.user.is_superuser
        else Workspace.objects.filter(
            assigned_users__user=request.user,
            assigned_users__is_admin=True
        )
    )

    # 🔹 Select workspace
    workspace = workspaces.filter(id=workspace_id).first() if workspace_id else None

    print(workspace)

    if not workspace:
        # No accessible workspace
        return render(request, "admin_map.html", {
            "workspaces": workspaces,
            "workspace": None,
            "spaces": None,
            "space": None,
            "seats": None,
        })

    # 🔹 Get spaces under the workspace
    spaces = workspace.spaces.filter(is_active=True).order_by("id")
    space = spaces.filter(id=space_id).first() if space_id else None

    # If no active spaces found
    if not spaces.exists():
        return render(request, "admin_map.html", {
            "workspaces": workspaces,
            "workspace": workspace,
            "spaces": None,
            "space": None,
            "seats": None,
        })

    # 🔹 Get seats (or None if no space)
    if space:
        seats = space.seats.filter(is_active=True).order_by("code")
    else:
        seats = None

    # 🔹 If there are seats, check reservations
    if seats:
        today = date.today()
        reservations = (
            Reservation.objects.filter(
                date=today,
                workspace=workspace,
                space=space,
                status="active"
            )
            .select_related("seat", "user")
        )

        seat_map = {r.seat.id: r for r in reservations}

        for seat in seats:
            r = seat_map.get(seat.id)
            seat.is_reserved = bool(r)
            seat.reserved_by = r.user.username if r else None

    context = {
        "workspaces": workspaces,
        "workspace": workspace,
        "spaces": spaces if spaces.exists() else None,
        "space": space,
        "seats": seats,
    }

    return render(request, "admin_map.html", context)


@require_POST
@login_required
def save_positions(request):
    if request.content_type != 'application/json':
        return HttpResponseBadRequest("Expected application/json")
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")
    updated = 0
    errors = []
    for item in payload:
        try:
            seat_id = int(item.get("id"))
            x = int(item.get("x"))
            y = int(item.get("y"))
            seat = Seat.objects.get(pk=seat_id)
            if not (request.user.is_superuser or get_user_is_admin(request.user, seat.space.workspace)):
                errors.append(f"No rights to modify seat {seat.code}")
                continue
            seat.x = x
            seat.y = y
            seat.save(update_fields=["x", "y"])
            updated += 1
        except Seat.DoesNotExist:
            errors.append(f"Seat {seat_id} not found")
        except Exception as e:
            errors.append(str(e))
    return JsonResponse({"ok": True, "updated": updated, "errors": errors})
# ----------------------------
# Booking APIs (status, book, cancel)
# ----------------------------

@login_required
@require_POST
def book_seat_api(request):
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

    seat = get_object_or_404(Seat, pk=seat_id, is_active=True)
    workspace = seat.space.workspace
    space = seat.space

    if not WorkspaceUser.objects.filter(user=request.user, workspace=workspace).exists():
        return JsonResponse({'ok': False, 'error': 'Not assigned to this workspace'}, status=403)

    today = date.today()
    pk_tz = pytz.timezone('Asia/Karachi')
    expires_at = timezone.make_aware(datetime.combine(today, RESERVATION_END), timezone=pk_tz)

    if Reservation.objects.filter(user=request.user, date=today, workspace=workspace, status='active').exists():
        return JsonResponse({'ok': False, 'error': 'You already have an active reservation today.'}, status=403)

    if Reservation.objects.filter(seat=seat, date=today, status='active').exists():
        return JsonResponse({'ok': False, 'error': 'Seat already reserved by another user.'}, status=403)

    reservation = Reservation.objects.create(
        user=request.user,
        workspace=workspace,
        space=space,
        seat=seat,
        date=today,
        expires_at=expires_at,
        status='active',
        is_active=True
    )

    ReservationLog.objects.create(
        reservation=reservation,
        user=request.user,
        seat_code=seat.code,
        action='created',
        timestamp=timezone.now()
    )

    return JsonResponse({'ok': True, 'message': f'Seat {seat.code} booked until 6:00 PM.', 'reservation_id': reservation.id})


@login_required
@require_POST
def cancel_reservation_api(request):
    if not in_booking_window():
        return JsonResponse({'ok': False, 'error': 'Cannot cancel outside booking window.'}, status=403)

    today = date.today()
    reservation = Reservation.objects.filter(user=request.user, date=today, is_active=True).first()

    if not reservation:
        return JsonResponse({'ok': False, 'error': 'No active reservation to cancel'}, status=404)

    ReservationLog.objects.create(
        reservation=reservation,
        user=request.user,
        seat_code=reservation.seat.code,
        action='cancelled',
        timestamp=timezone.now()
    )

    reservation.is_active = False
    reservation.status = 'cancelled'
    reservation.save(update_fields=['is_active', 'status'])

    return JsonResponse({'ok': True, 'message': 'Reservation cancelled successfully.'})
