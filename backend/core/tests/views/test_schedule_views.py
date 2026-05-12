"""Tests para vistas de horarios"""
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import schedules_view


class TestScheduleViews:
    """Tests para vistas de horarios"""

    def test_list_schedules_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/schedules/")

        response = schedules_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_schedules_authenticated(self):
        factory = APIRequestFactory()
        request = factory.get("/api/schedules/?grado_id=grado-1")
        request.usuario = SimpleNamespace(id="user-1", activo=True, nombre="Admin", apellido="Test", email="admin@test.com")

        payload = {"resumen": [], "calendario": [], "proximas_clases": [], "permisos": {}}

        with patch("core.views.SchedulesService.build_schedules_page", return_value=payload) as build_schedules_page:
            response = schedules_view(request)

        build_schedules_page.assert_called_once_with(request.usuario, grado_id="grado-1")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == payload
