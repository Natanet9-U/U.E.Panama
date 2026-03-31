from django.urls import path
from . import views

urlpatterns = [
    path('estudiantes/', views.listar_estudiantes, name='listar_estudiantes'),
    
    path('estudiantes/curso/<str:grado_id>/', views.estudiantes_por_curso, name='estudiantes_por_curso'),
    
    path('asistencias/registrar/', views.registrar_asistencia, name='registrar_asistencia'),
]