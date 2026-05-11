"""Tests para vistas de cursos"""
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import courses_view


class TestCourseViews:
    """Tests para vistas de cursos"""

    def test_list_courses_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/courses/")

        response = courses_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_courses_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/courses/?query=Mat&page=3&page_size=4")
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        payload = {"resumen": [], "cursos": [], "paginacion": {}, "filtros": {}, "permisos": {}}

        with patch("core.views.CoursesService.build_courses_page", return_value=payload) as build_courses_page:
            response = courses_view(request)

        build_courses_page.assert_called_once_with(request.usuario, query="Mat", page="3", page_size="4")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload

    def test_create_course_authenticated(self):
        factory = APIRequestFactory()
        request = factory.post("/api/courses/", {"area_id": "area-1", "grado_id": "grado-1"}, format="json")
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        created_payload = {"id": "course-1"}

        with patch("core.views.CoursesService.create_course", return_value=created_payload) as create_course:
            response = courses_view(request)

        create_course.assert_called_once()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["curso"] == created_payload
