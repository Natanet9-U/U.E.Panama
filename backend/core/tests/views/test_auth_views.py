"""Tests para vistas de autenticación"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import Usuarios
from core.views import health_view, login_view, logout_view, me_view


class TestAuthViews:
    """Tests para vistas de autenticación"""

    def test_health_view(self):
        factory = APIRequestFactory()
        request = factory.get("/api/health/")

        response = health_view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"

    def test_login_missing_fields(self):
        factory = APIRequestFactory()
        request = factory.post("/api/login/", {"email": ""}, format="json")

        response = login_view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_with_valid_credentials(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/login/",
            {"email": "test@test.com", "password": "TestPassword123!"},
            format="json",
        )
        usuario = MagicMock(
            id="user-1",
            nombre="Ana",
            apellido="Perez",
            email="test@test.com",
            activo=True,
            password_hash="hash",
        )

        with patch("core.views.Usuarios.objects.get", return_value=usuario), \
                patch("core.views.check_password", return_value=True), \
                patch("core.views.build_token", return_value="signed-token"):
            response = login_view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["token"] == "signed-token"
        assert response.data["usuario"]["email"] == "test@test.com"

    def test_login_inactive_user(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/login/",
            {"email": "inactive@test.com", "password": "TestPassword123!"},
            format="json",
        )
        usuario = MagicMock(id="user-2", nombre="Ana", apellido="Perez", email="inactive@test.com", activo=False, password_hash="hash")

        with patch("core.views.Usuarios.objects.get", return_value=usuario), \
                patch("core.views.check_password", return_value=True):
            response = login_view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_login_invalid_password(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/login/",
            {"email": "test@test.com", "password": "wrong"},
            format="json",
        )
        usuario = MagicMock(id="user-1", nombre="Ana", apellido="Perez", email="test@test.com", activo=True, password_hash="hash")

        with patch("core.views.Usuarios.objects.get", return_value=usuario), \
                patch("core.views.check_password", return_value=False):
            response = login_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_user_not_found(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/login/",
            {"email": "missing@test.com", "password": "wrong"},
            format="json",
        )

        with patch("core.views.Usuarios.objects.get", side_effect=Usuarios.DoesNotExist):
            response = login_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_requires_auth(self):
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")

        response = me_view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_user_payload(self):
        factory = APIRequestFactory()
        request = factory.get("/api/auth/me/")
        request.usuario = SimpleNamespace(id="user-1", nombre="Ana", apellido="Perez", email="test@test.com", activo=True)

        response = me_view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["usuario"]["email"] == "test@test.com"

    def test_logout(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/logout/")

        response = logout_view(request)

        assert response.status_code == status.HTTP_200_OK
