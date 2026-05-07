from django.urls import path
from .views import courses_view, dashboard_view, grades_view, health_view, login_view, logout_view, me_view, reports_view, schedules_view, students_view

urlpatterns = [
    path('health/', health_view, name='health'),
    path('auth/login/', login_view, name='auth_login'),
    path('auth/me/', me_view, name='auth_me'),
    path('auth/logout/', logout_view, name='auth_logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('students/', students_view, name='students'),
    path('courses/', courses_view, name='courses'),
    path('grades/', grades_view, name='grades'),
    path('reports/', reports_view, name='reports'),
    path('schedules/', schedules_view, name='schedules'),
    path('login/', login_view, name='login'),
]