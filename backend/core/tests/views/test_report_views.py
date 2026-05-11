"""Tests para vistas de reportes"""
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import reports_view


class TestReportViews:
    """Tests para vistas de reportes"""

    def test_list_reports_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/reports/")

        response = reports_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_reports_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/reports/?periodo_id=period-1")
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        payload = {"resumen": [], "reportes": [], "top_estudiantes": [], "alertas": [], "cursos": [], "filtros": {}, "permisos": {}}

        with patch("core.views.ReportsService.build_reports_page", return_value=payload) as build_reports_page:
            response = reports_view(request)

        build_reports_page.assert_called_once_with(request.usuario, periodo_id="period-1")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload
