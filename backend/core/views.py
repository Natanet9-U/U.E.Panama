from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import Usuarios
from .auth_utils import build_token


def _user_payload(usuario):
    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "activo": bool(usuario.activo) if usuario.activo is not None else True,
    }


@api_view(["GET"])
def health_view(request):
    return Response({"status": "ok"}, status=200)

@api_view(["POST"])
def login_view(request):
    email_recibido = request.data.get("email")
    password_recibida = request.data.get("password")

    if not email_recibido or not password_recibida:
        return Response(
            {"error": "Debes enviar email y password"},
            status=400,
        )

    try:
        usuario = Usuarios.objects.get(email__iexact=email_recibido)

        if check_password(password_recibida, usuario.password_hash):
            if usuario.activo is False:
                return Response({"error": "Usuario inactivo"}, status=403)

            token = build_token(usuario.id)

            return Response({
                "mensaje": "Login exitoso",
                "token": token,
                "usuario": _user_payload(usuario),
            }, status=200)

        return Response({"error": "Credenciales invalidas"}, status=401)

    except Usuarios.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=401)


@api_view(["GET"])
def me_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    return Response({"usuario": _user_payload(usuario)}, status=200)


@api_view(["POST"])
def logout_view(request):
    # Token firmado es stateless; el cliente elimina el token localmente.
    return Response({"mensaje": "Sesion cerrada"}, status=200)