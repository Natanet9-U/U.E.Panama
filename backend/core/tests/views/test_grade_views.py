"""Tests para vistas de calificaciones"""
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import grades_view


class TestGradeViews:
    """Tests para vistas de calificaciones"""

    def test_list_grades_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/grades/")

        response = grades_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_grades_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/grades/?query=Ana&periodo_id=period-1&page=2&page_size=7")
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        payload = {"resumen": [], "calificaciones": [], "paginacion": {}, "filtros": {}, "permisos": {}}

        with patch("core.views.GradesService.build_grades_page", return_value=payload) as build_grades_page:
            response = grades_view(request)

        build_grades_page.assert_called_once_with(request.usuario, query="Ana", periodo_id="period-1", page="2", page_size="7")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload
