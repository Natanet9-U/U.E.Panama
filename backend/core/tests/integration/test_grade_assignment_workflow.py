"""Tests de integración para flujos de calificaciones"""
import pytest
from rest_framework import status

from core.tests.factories import UsuarioFactory


@pytest.mark.django_db
class TestGradeAssignmentWorkflow:
    """Tests de integración para asignación de calificaciones"""

    def test_teacher_can_assign_grades(self, teacher_client, student_user):
        """Verifica que un docente puede asignar calificaciones"""
        # 1. Docente se loguea (ya autenticado en teacher_client)
        
        # 2. Intenta asignar una calificación
        # grade_data = {
        #     'student_id': student_user.id,
        #     'grade': 95,
        # }
        # response = teacher_client.post('/api/grades/', grade_data)
        
        # assert response.status_code == status.HTTP_201_CREATED


# Agrega más flujos de integración
