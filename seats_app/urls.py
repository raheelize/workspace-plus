from django.urls import path
from . import views

# app_name = 'seats'

urlpatterns = [
    path('', views.index, name='index'),
    path('workspace/', views.workspace, name='workspace'),
    path('admin-map/', views.admin_map, name='admin_map'),
    path('api/save-positions/', views.save_positions, name='save_positions'),
    path('api/book-seat/', views.book_seat_api, name='book_seat_api'),
    path('api/cancel-booking/', views.cancel_reservation_api, name='cancel_reservation_api'),

    

    # Workspace CRUD
    path('workspace/create/', views.admin_workspace_crud, name='admin_create_workspace'),
    path('workspace/edit/<int:pk>/', views.admin_workspace_crud, name='admin_edit_workspace'),
    path('workspace/delete/<int:pk>/', views.admin_workspace_crud, name='admin_delete_workspace'),

    # Space CRUD
    path('space/create/<int:workspace_id>/', views.admin_space_crud, name='admin_create_space'),
    path('space/edit/<int:pk>/', views.admin_space_crud, name='admin_edit_space'),
    path('space/delete/<int:pk>/', views.admin_space_crud, name='admin_delete_space'),

    # Seat CRUD
    path('seat/create/<int:space_id>/', views.admin_seat_crud, name='admin_create_seat'),
    path('seat/edit/<int:pk>/', views.admin_seat_crud, name='admin_edit_seat'),
    path('seat/delete/<int:pk>/', views.admin_seat_crud, name='admin_delete_seat'),
]
