from django.urls import path
from .views import health_view, login_view, logout_view, me_view

urlpatterns = [
    path('health/', health_view, name='health'),
    path('auth/login/', login_view, name='auth_login'),
    path('auth/me/', me_view, name='auth_me'),
    path('auth/logout/', logout_view, name='auth_logout'),
    path('login/', login_view, name='login'),
]