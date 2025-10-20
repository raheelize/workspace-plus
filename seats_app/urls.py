from django.urls import path
from . import views

app_name = 'seats'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/status/', views.seat_status_api, name='seat_status_api'),
    path('api/book/', views.book_seat_api, name='book_seat_api'),
    path('api/cancel/', views.cancel_reservation_api, name='cancel_reservation_api'),
    path('admin-map/', views.admin_map, name='admin_map'),
    path('api/save-positions/', views.save_positions, name='save_positions'),
    # path('register/', views.register_view, name='register'),
]