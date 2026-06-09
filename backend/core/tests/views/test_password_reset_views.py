from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.views import forgot_password_view, reset_password_view


class TestForgotPasswordView:

    def test_missing_email(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/forgot-password/", {}, format="json")
        response = forgot_password_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/forgot-password/", {"email": "admin@test.com"}, format="json")
        with patch("core.views.AuthService.solicitar_reset", return_value="reset_token"):
            response = forgot_password_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_email_not_found(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/forgot-password/", {"email": "no@test.com"}, format="json")
        with patch("core.views.AuthService.solicitar_reset", return_value=None):
            response = forgot_password_view(request)
        assert response.status_code == status.HTTP_200_OK


class TestResetPasswordView:

    def test_missing_fields(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/reset-password/", {}, format="json")
        response = reset_password_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_success(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/reset-password/", {"token": "valid", "new_password": "new_pass_123"}, format="json")
        with patch("core.views.AuthService.reset_password", return_value={"mensaje": "Contrasena actualizada"}):
            response = reset_password_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_token(self):
        factory = APIRequestFactory()
        request = factory.post("/api/auth/reset-password/", {"token": "bad", "new_password": "new_pass_123"}, format="json")
        with patch("core.views.AuthService.reset_password", side_effect=ValueError("Token invalido")):
            response = reset_password_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
