from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from django.contrib.auth.hashers import check_password, make_password
from .models import Usuarios
from .auth_utils import build_token
from .services.dashboard_service import DashboardService
from .services.courses_service import CoursesService
from .services.grades_service import GradesService
from .services.docentes_service import DocentesService
from .services.reports_service import ReportsService
from .services.schedules_service import SchedulesService
from .services.students_service import StudentsService
from .services.enrollment_service import EnrollmentService
from .services.access_service import AccessControlService
from .services.attendance_service import AttendanceService
from .models import DocenteAsignacion
from .models import DimensionesEvaluacion, Estudiantes, Notas, NotaDetalle, Periodos
from .models import Actividades, ActividadNotas
from uuid import uuid4
from django.utils import timezone



def _user_payload(usuario):
    roles = []
    try:
        roles = sorted(AccessControlService().get_role_names(usuario))
    except Exception:
        roles = []

    cargo = roles[0] if roles else ""
    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "activo": bool(usuario.activo) if usuario.activo is not None else True,
        "roles": roles,
        "rol": cargo,
        "cargo": cargo,
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

            # Precalienta cache del dashboard para mejorar tiempo de primera carga.
            try:
                DashboardService().warm_cache_for_user(usuario)
            except Exception:
                pass

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
def attendance_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    service = AttendanceService()

    if request.method == "POST":
        try:
            asignacion_id = request.data.get("asignacion_id")
            fecha = request.data.get("fecha")
            estados_map = request.data.get("estados")
            created = service.mark_attendance(usuario, asignacion_id, fecha, estados_map)
            return Response({"mensaje": "Asistencias registradas", "ids": created}, status=201)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)

    # GET: listar asistencias por asignacion y fecha
    asignacion_id = request.query_params.get("asignacion_id")
    fecha = request.query_params.get("fecha")
    if not asignacion_id or not fecha:
        return Response({"error": "Debe enviar asignacion_id y fecha como query params"}, status=400)

    registros = []

    # consulta directa ligera
    from .models import Asistencias
    grado_id = DocenteAsignacion.objects.filter(id=asignacion_id).values_list("grado_id", flat=True).first()
    qs = Asistencias.objects.filter(fecha=fecha, estudiante__grado_id=grado_id)
    for r in qs.select_related("estudiante__usuario"):
        registros.append({
            "estudiante_id": str(r.estudiante_id),
            "nombre": f"{r.estudiante.nombres} {r.estudiante.primer_apellido}",
            "estado": r.estado,
        })

    return Response({"asistencias": registros}, status=200)


@api_view(["POST"])
def licencias_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    service = AttendanceService()
    try:
        licencia = service.create_licencia(usuario, request.data)
        return Response({"mensaje": "Licencia creada", "licencia": licencia}, status=201)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)


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
def docentes_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    service = DocentesService()

    if request.method == "POST":
        try:
            docente = service.create_docente(usuario, request.data)
            return Response({"mensaje": "Docente creado", "docente": docente}, status=201)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=403)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)

    query = request.query_params.get("query") or request.query_params.get("search")
    page = request.query_params.get("page", 1)
    page_size = request.query_params.get("page_size", 8)
    payload = service.build_docentes_page(usuario, query=query, page=page, page_size=page_size)
    return Response(payload, status=200)


@api_view(["GET"])
def enrollment_search_view(request):
    """Search for existing students by RUDE for re-enrollment."""
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    rude = request.query_params.get("rude", "").strip()
    if not rude:
        return Response({"error": "Debes proporcionar un R.U.D.E."}, status=400)

    service = EnrollmentService()
    resultado = service.search_existing_student(rude)

    if resultado is None:
        return Response({"encontrado": False, "mensaje": "Estudiante no encontrado"}, status=200)

    return Response({"encontrado": True, "estudiante": resultado}, status=200)


@api_view(["POST"])
def enrollment_new_view(request):
    """Enroll a new student or re-enroll an existing one."""
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    service = EnrollmentService()

    try:
        resultado = service.enroll_new_student(usuario, request.data)
        return Response(resultado, status=201)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["POST"])
def enrollment_re_enroll_view(request):
    """Re-enroll an existing inactive student."""
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    rude = request.data.get("rude")
    new_grado_id = request.data.get("grado_id")

    if not rude or not new_grado_id:
        return Response({"error": "Debes enviar rude y grado_id"}, status=400)

    service = EnrollmentService()

    try:
        resultado = service.re_enroll_existing_student(usuario, rude, new_grado_id)
        return Response(resultado, status=200)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["GET"])
def enrollment_catalogs_view(request):
    """Get enrollment catalogs (grades, tutores)."""
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    service = EnrollmentService()
    catalogs = service.get_enrollment_catalogs(usuario)
    return Response(catalogs, status=200)


@api_view(["GET"])
def search_tutor_by_ci_view(request):
    """Search for an existing tutor by CI."""
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    ci = request.query_params.get("ci", "").strip()
    if not ci:
        return Response({"error": "Debes proporcionar un CI"}, status=400)

    from .models import Tutores
    tutor = Tutores.objects.filter(ci__iexact=ci).order_by("nombre", "id").first()
    if tutor:
        return Response({
            "encontrado": True,
            "tutor": {
                "id": str(tutor.id),
                "nombre": tutor.nombre,
                "apellido": tutor.apellido or "",
                "ci": tutor.ci,
                "telefono": tutor.telefono or "",
                "ocupacion": tutor.ocupacion or "",
                "direccion": tutor.direccion or "",
            }
        }, status=200)

    return Response({"encontrado": False}, status=200)


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


@api_view(["POST"])
def grades_update_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    asignacion_id = request.data.get("asignacion_id")
    periodo_id = request.data.get("periodo_id")
    payload = request.data.get("notas")

    if not asignacion_id or not periodo_id or payload is None:
        return Response({"error": "Debe enviar asignacion_id, periodo_id y notas"}, status=400)

    try:
        updated = GradesService().update_student_grades(usuario, asignacion_id, periodo_id, payload)
        return Response({"mensaje": "Notas actualizadas", "updated": updated}, status=200)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)
    except Exception as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["POST"])
def recompute_actividades_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    asignacion_id = request.data.get("asignacion_id")
    periodo_id = request.data.get("periodo_id")
    if not asignacion_id or not periodo_id:
        return Response({"error": "Debe enviar asignacion_id y periodo_id"}, status=400)

    try:
        updated = GradesService().recompute_from_actividades(usuario, asignacion_id, periodo_id)
        return Response({"mensaje": "Recomputo completado", "updated": updated}, status=200)
    except PermissionError as exc:
        return Response({"error": str(exc)}, status=403)
    except Exception as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["GET"])
def course_detail_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    asignacion_id = request.query_params.get("asignacion_id")
    periodo_id = request.query_params.get("periodo_id")
    fecha = request.query_params.get("fecha")

    if not asignacion_id:
        return Response({"error": "Debe enviar asignacion_id como query param"}, status=400)

    # obtener grado y estudiantes
    grado_id = DocenteAsignacion.objects.filter(id=asignacion_id).values_list("grado_id", flat=True).first()
    if not grado_id:
        return Response({"error": "Asignacion no encontrada"}, status=404)

    students_qs = Estudiantes.objects.filter(grado_id=grado_id).select_related("usuario")
    estudiantes = [{"id": str(s.id), "nombre": f"{s.nombres} {s.primer_apellido}"} for s in students_qs]

    dimensiones = []
    periodos = []
    try:
        # infer gestion from grado via first periodo if not provided
        gestion = None
        if periodo_id:
            gestion = Periodos.objects.filter(id=periodo_id).values_list("gestion", flat=True).first()
        if not gestion:
            gestion = Periodos.objects.order_by("-gestion").values_list("gestion", flat=True).first()

        periodos_qs = Periodos.objects.order_by("-gestion", "-numero")
        periodos = [{"id": str(p.id), "nombre": f"{p.nombre} {p.gestion}", "numero": p.numero, "gestion": p.gestion, "activo": p.activo} for p in periodos_qs]

        dimensiones_qs = DimensionesEvaluacion.objects.filter(gestion=gestion, activo=True).order_by("orden")
        dimensiones = [{"id": str(d.id), "nombre": d.nombre, "puntaje_maximo": d.puntaje_maximo, "descripcion": d.descripcion, "orden": d.orden, "activo": d.activo} for d in dimensiones_qs]
    except Exception:
        dimensiones = []
        periodos = []

    notas = []
    if periodo_id:
        qs = Notas.objects.filter(asignacion_id=asignacion_id, periodo_id=periodo_id).select_related("estudiante__usuario")
        for n in qs:
            detalles = []
            for nd in NotaDetalle.objects.filter(nota=n).select_related("dimension"):
                detalles.append({"dimension_id": str(nd.dimension_id), "valor": nd.valor})

            notas.append({"estudiante_id": str(n.estudiante_id), "total": n.total, "detalles": detalles, "observaciones": n.observaciones})

    # actividades y notas por actividad
    actividades = []
    try:
        acts_qs = Actividades.objects.filter(asignacion_id=asignacion_id).order_by("orden", "fecha")
        for a in acts_qs:
            actividades.append({"id": str(a.id), "nombre": a.nombre, "puntaje_maximo": a.puntaje_maximo, "dimension_id": str(a.dimension_id) if a.dimension_id else None, "dimension_nombre": a.dimension.nombre if a.dimension_id else None, "fecha": a.fecha})

        # cargar notas por actividad
        actividad_notas_map = {}
        for an in ActividadNotas.objects.filter(actividad__asignacion_id=asignacion_id).select_related("actividad", "estudiante"):
            key = str(an.actividad_id)
            actividad_notas_map.setdefault(key, {})[str(an.estudiante_id)] = an.valor
    except Exception:
        actividades = []
        actividad_notas_map = {}

    if not periodo_id:
        # compute trimestral and overall summaries
        try:
            resumen = GradesService().compute_trimestral_and_overall(asignacion_id)
        except Exception:
            resumen = []
        return Response({"estudiantes": estudiantes, "dimensiones": dimensiones, "periodos": periodos, "notas": notas, "resumen": resumen, "actividades": actividades, "actividad_notas": actividad_notas_map}, status=200)

    return Response({"estudiantes": estudiantes, "dimensiones": dimensiones, "periodos": periodos, "notas": notas, "actividades": actividades, "actividad_notas": actividad_notas_map}, status=200)


@api_view(["GET", "POST"])
def actividades_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    # POST: crear actividad
    if request.method == "POST":
        asignacion_id = request.data.get("asignacion_id")
        nombre = request.data.get("nombre")
        puntaje_maximo = request.data.get("puntaje_maximo") or 100
        dimension_id = request.data.get("dimension_id")
        fecha = request.data.get("fecha")

        if not asignacion_id or not nombre or not dimension_id:
            return Response({"error": "Debe enviar asignacion_id, nombre y dimension_id"}, status=400)

        assigned = AccessControlService().get_assigned_assignment_ids(usuario)
        if not (AccessControlService().can_view_all_academic_data(usuario) or (asignacion_id in assigned)):
            return Response({"error": "No tienes permisos para crear actividades en esta asignación"}, status=403)

        dimension = DimensionesEvaluacion.objects.filter(id=dimension_id).first()
        if dimension is None:
            return Response({"error": "La dimensión seleccionada no existe"}, status=400)

        dimension_nombre = (dimension.nombre or "").strip().lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        if dimension_nombre.startswith("autoevalu"):
            return Response({"error": "La autoevaluación se registra como una nota fija del trimestre"}, status=400)

        act = Actividades.objects.create(
            id=uuid4(),
            asignacion_id=asignacion_id,
            nombre=nombre,
            puntaje_maximo=int(puntaje_maximo),
            dimension_id=dimension_id,
            fecha=fecha,
            created_at=timezone.now(),
        )

        return Response({"mensaje": "Actividad creada", "actividad": {"id": str(act.id), "nombre": act.nombre, "puntaje_maximo": act.puntaje_maximo, "dimension_id": str(act.dimension_id) if act.dimension_id else None, "dimension_nombre": act.dimension.nombre if act.dimension_id else None}}, status=201)

    # GET: listar actividades por asignacion
    asignacion_id = request.query_params.get("asignacion_id")
    if not asignacion_id:
        return Response({"error": "Debe enviar asignacion_id como query param"}, status=400)

    acts = []
    for a in Actividades.objects.filter(asignacion_id=asignacion_id).order_by("orden", "fecha"):
        acts.append({"id": str(a.id), "nombre": a.nombre, "puntaje_maximo": a.puntaje_maximo, "dimension_id": str(a.dimension_id) if a.dimension_id else None, "dimension_nombre": a.dimension.nombre if a.dimension_id else None, "fecha": a.fecha})

    return Response({"actividades": acts}, status=200)


@api_view(["DELETE"])
def actividad_delete_view(request, actividad_id):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    actividad = Actividades.objects.filter(id=actividad_id).select_related("asignacion").first()
    if not actividad:
        return Response({"error": "Actividad no encontrada"}, status=404)

    assigned = AccessControlService().get_assigned_assignment_ids(usuario)
    asignacion_id = str(actividad.asignacion_id)
    if not (AccessControlService().can_view_all_academic_data(usuario) or (asignacion_id in assigned)):
        return Response({"error": "No tienes permisos para eliminar esta actividad"}, status=403)

    ActividadNotas.objects.filter(actividad_id=actividad.id).delete()
    actividad.delete()

    return Response({"mensaje": "Actividad eliminada"}, status=200)


@api_view(["POST"])
def actividades_notas_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    actividad_id = request.data.get("actividad_id")
    notas = request.data.get("notas")
    if not actividad_id or notas is None:
        return Response({"error": "Debe enviar actividad_id y notas"}, status=400)

    # permission check: teacher must be owner of the actividad's asignacion
    asignacion_id = Actividades.objects.filter(id=actividad_id).values_list("asignacion_id", flat=True).first()
    if not asignacion_id:
        return Response({"error": "Actividad no encontrada"}, status=404)

    assigned = AccessControlService().get_assigned_assignment_ids(usuario)
    if not (AccessControlService().can_view_all_academic_data(usuario) or (asignacion_id in assigned)):
        return Response({"error": "No tienes permisos para modificar notas en esta asignación"}, status=403)

    updated = []
    for estudiante_id, valor in (notas or {}).items():
        an, created = ActividadNotas.objects.update_or_create(
            actividad_id=actividad_id,
            estudiante_id=estudiante_id,
            defaults={"valor": int(valor or 0), "created_at": timezone.now()},
        )
        updated.append({"estudiante_id": str(estudiante_id), "valor": an.valor})

    return Response({"mensaje": "Notas actualizadas", "updated": updated}, status=200)


@api_view(["GET"])
def actividades_notas_estudiante_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    asignacion_id = request.query_params.get("asignacion_id")
    estudiante_id = request.query_params.get("estudiante_id")
    if not asignacion_id or not estudiante_id:
        return Response({"error": "Debe enviar asignacion_id y estudiante_id"}, status=400)

    result = {}
    for an in ActividadNotas.objects.filter(actividad__asignacion_id=asignacion_id, estudiante_id=estudiante_id).select_related('actividad'):
        result[str(an.actividad_id)] = an.valor

    return Response({"notas": result}, status=200)


@api_view(["GET"])
def reports_download_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    periodo_id = request.query_params.get("periodo_id") or request.query_params.get("periodo")
    trimestre = request.query_params.get("trimestre")
    kwargs = {"periodo_id": periodo_id}
    if trimestre:
        kwargs["trimestre"] = trimestre
    document_bytes = ReportsService().build_report_document(usuario, **kwargs)
    filename = f"informe_reporte_{timezone.localdate().strftime('%Y%m%d')}.docx"

    response = HttpResponse(
        document_bytes,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


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


@api_view(["POST"])
def change_password_view(request):
    usuario = getattr(request, "usuario", None)
    if usuario is None:
        return Response({"error": "No autorizado"}, status=401)

    current = request.data.get("current_password") or request.data.get("password_actual")
    new = request.data.get("new_password") or request.data.get("password_nueva")

    if not current or not new:
        return Response({"error": "Debe enviar contraseña actual y nueva"}, status=400)

    if not check_password(current, usuario.password_hash):
        return Response({"error": "Contraseña actual incorrecta"}, status=403)

    # Opcional: validar longitud mínima
    if len(new) < 6:
        return Response({"error": "La contraseña nueva debe tener al menos 6 caracteres"}, status=400)

    usuario.password_hash = make_password(new)
    usuario.save()

    return Response({"mensaje": "Contraseña actualizada"}, status=200)
