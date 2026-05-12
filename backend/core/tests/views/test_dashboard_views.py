"""Tests para vistas de dashboard"""
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import dashboard_view


class TestDashboardViews:
    """Tests para vistas de dashboard"""

    def test_dashboard_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/")

        response = dashboard_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_returns_payload(self):
        factory = APIRequestFactory()
        request = factory.get("/api/dashboard/")
        request.usuario = SimpleNamespace(id="user-1", nombre="Ana", apellido="Perez", email="test@test.com", activo=True)

        payload = {"resumen": [], "asistencia_semanal": [], "periodo_activo": None}

        with patch("core.views.DashboardService.build_dashboard", return_value=payload) as build_dashboard:
            response = dashboard_view(request)

        build_dashboard.assert_called_once()
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload
