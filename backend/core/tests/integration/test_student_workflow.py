"""Tests de integración para flujos de estudiantes"""
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import grades_view, login_view


class TestStudentWorkflow:
    """Tests de integración para el flujo completo de estudiantes"""

    def test_student_can_login_and_view_grades(self, student_user):
        """Verifica que un estudiante puede loguearse y ver calificaciones"""
        factory = APIRequestFactory()
        login_request = factory.post('/api/login/', {'email': student_user.email, 'password': 'StudentPassword123!'}, format='json')
        grades_request = factory.get('/api/grades/')

        with patch("core.views.Usuarios.objects.get", return_value=student_user), \
             patch("core.views.check_password", return_value=True), \
             patch("core.views.build_token", return_value="signed-token"), \
             patch("core.views.GradesService.build_grades_page", return_value={"calificaciones": []}):
            response = login_view(login_request)

        assert response.status_code == status.HTTP_200_OK
        token = response.data.get('token')
        assert token is not None

        grades_request.usuario = student_user
        grades_request.query_params = grades_request.GET
        with patch("core.views.GradesService.build_grades_page", return_value={"calificaciones": []}):
            grades_response = grades_view(grades_request)

        assert grades_response.status_code == status.HTTP_200_OK
        assert grades_response.data["calificaciones"] == []


# Agrega más flujos de integración
