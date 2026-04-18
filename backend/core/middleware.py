import time

from django.http import JsonResponse

from .auth_utils import decode_token
from .models import Usuarios


class LogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        print(f"-> {request.method} {request.path}")

        response = self.get_response(request)

        duration = time.time() - start
        print(f"<- {response.status_code} in {duration:.2f}s")
        return response


class ErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            return JsonResponse(
                {
                    "error": "Error interno",
                    "detalle": str(exc),
                },
                status=500,
            )


class AuthMiddleware:
    PUBLIC_PATHS = {
        "/api/health/",
        "/api/auth/login/",
        "/api/login/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        if request.path in self.PUBLIC_PATHS:
            return self.get_response(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "No autorizado"}, status=401)

        token = auth_header.split(" ", 1)[1].strip()
        user_id, token_error = decode_token(token)
        if token_error == "TOKEN_EXPIRED":
            return JsonResponse({"error": "Token expirado"}, status=401)
        if token_error == "TOKEN_INVALID":
            return JsonResponse({"error": "Token invalido"}, status=401)

        try:
            usuario = Usuarios.objects.get(id=user_id)
        except Usuarios.DoesNotExist:
            return JsonResponse({"error": "Usuario no encontrado"}, status=401)

        if usuario.activo is False:
            return JsonResponse({"error": "Usuario inactivo"}, status=403)

        request.usuario = usuario
        return self.get_response(request)

