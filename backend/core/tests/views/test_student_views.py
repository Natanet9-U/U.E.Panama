"""Tests para vistas de estudiantes"""
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import students_view


class TestStudentViews:
    """Tests para vistas de estudiantes"""

    def test_list_students_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/")

        response = students_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_students_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/students/?query=Ana&page=2&page_size=5")
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        payload = {"resumen": [], "estudiantes": [], "paginacion": {}, "filtros": {}, "permisos": {}}

        with patch("core.views.StudentsService.build_students_page", return_value=payload) as build_students_page:
            response = students_view(request)

        build_students_page.assert_called_once_with(query="Ana", grado_id=None, page="2", page_size="5")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload

    def test_create_student_authenticated(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/students/",
            {
                "nombres": "Nuevo",
                "primer_apellido": "Estudiante",
                "segundo_apellido": "Test",
                "ci": "8765432",
                "email": "nuevo@test.com",
                "grado_id": "grado-1",
            },
            format="json",
        )
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        created_payload = {"id": "student-1", "nombre": "Nuevo Estudiante"}

        with patch("core.views.StudentsService.create_student", return_value=created_payload) as create_student:
            response = students_view(request)

        create_student.assert_called_once()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["estudiante"] == created_payload

    def test_create_student_permission_denied(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/", {"nombres": "Nuevo"}, format="json")
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        with patch("core.views.StudentsService.create_student", side_effect=PermissionError("sin permisos")):
            response = students_view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_student_invalid_payload(self):
        factory = APIRequestFactory()
        request = factory.post("/api/students/", {"nombres": "Nuevo"}, format="json")
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        with patch("core.views.StudentsService.create_student", side_effect=ValueError("datos invalidos")):
            response = students_view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
