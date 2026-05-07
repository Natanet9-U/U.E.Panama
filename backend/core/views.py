from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import Usuarios
from .auth_utils import build_token
from .services.dashboard_service import DashboardService
from .services.courses_service import CoursesService
from .services.grades_service import GradesService
from .services.reports_service import ReportsService
from .services.schedules_service import SchedulesService
from .services.students_service import StudentsService
from .services.access_service import AccessControlService


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


@api_view(["GET"])
def dashboard_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    dashboard = DashboardService().build_dashboard(usuario)
    return Response(dashboard, status=200)


@api_view(["GET", "POST"])
def students_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    service = StudentsService()
    service.usuario = usuario

    if request.method == "POST":
        try:
            estudiante = service.create_student(usuario, request.data)
            return Response({"mensaje": "Estudiante creado", "estudiante": estudiante}, status=201)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)

    query = request.query_params.get("query") or request.query_params.get("search")
    grado_id = request.query_params.get("grado_id") or request.query_params.get("grado")
    page = request.query_params.get("page", 1)
    page_size = request.query_params.get("page_size", 8)

    payload = service.build_students_page(
        query=query,
        grado_id=grado_id,
        page=page,
        page_size=page_size,
    )
    return Response(payload, status=200)


@api_view(["GET", "POST"])
def courses_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    if request.method == "POST":
        try:
            curso = CoursesService().create_course(usuario, request.data)
            return Response({"mensaje": "Curso creado", "curso": curso}, status=201)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)

    query = request.query_params.get("query") or request.query_params.get("search")
    page = request.query_params.get("page", 1)
    page_size = request.query_params.get("page_size", 6)

    payload = CoursesService().build_courses_page(
        usuario,
        query=query,
        page=page,
        page_size=page_size,
    )
    return Response(payload, status=200)


@api_view(["GET"])
def grades_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    query = request.query_params.get("query") or request.query_params.get("search")
    periodo_id = request.query_params.get("periodo_id") or request.query_params.get("periodo")
    page = request.query_params.get("page", 1)
    page_size = request.query_params.get("page_size", 10)

    payload = GradesService().build_grades_page(
        usuario,
        query=query,
        periodo_id=periodo_id,
        page=page,
        page_size=page_size,
    )
    return Response(payload, status=200)


@api_view(["GET"])
def reports_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    periodo_id = request.query_params.get("periodo_id") or request.query_params.get("periodo")
    payload = ReportsService().build_reports_page(usuario, periodo_id=periodo_id)
    return Response(payload, status=200)


@api_view(["GET"])
def schedules_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    grado_id = request.query_params.get("grado_id")
    payload = SchedulesService().build_schedules_page(usuario, grado_id=grado_id)
    return Response(payload, status=200)


@api_view(["POST"])
def logout_view(request):
    # Token firmado es stateless; el cliente elimina el token localmente.
    return Response({"mensaje": "Sesion cerrada"}, status=200)