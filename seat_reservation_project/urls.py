from django.urls import path, include
from django.contrib import admin
from . import views 
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('seats_app.urls')),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', views.register_view, name='register'),  # custom register
    path('accounts/login/', views.login_view, name='login'), 
    path('logout', views.logout_view, name='logout'),
]
