from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone

from ..models import Asistencias, Estudiantes, Grados, Notas, Periodos, Roles, UsuarioRoles, Usuarios
from .access_service import AccessControlService


class StudentsService:
    def __init__(self):
        self.access_service = AccessControlService()

    def build_students_page(self, *, query=None, grado_id=None, page=1, page_size=8):
        queryset = Estudiantes.objects.select_related("grado", "usuario").order_by("nombres", "primer_apellido")
        queryset = self.access_service.filter_students_queryset(queryset, self._current_user)

        if query:
            queryset = queryset.filter(
                Q(nombres__icontains=query)
                | Q(primer_apellido__icontains=query)
                | Q(segundo_apellido__icontains=query)
                | Q(ci__icontains=query)
                | Q(usuario__email__icontains=query)
            )

        if grado_id:
            queryset = queryset.filter(grado_id=grado_id)

        total_estudiantes = queryset.count()
        page = max(int(page or 1), 1)
        page_size = max(min(int(page_size or 8), 50), 1)
        offset = (page - 1) * page_size

        periodo_activo = self._get_periodo_activo()
        estudiante_ids = list(queryset.values_list("id", flat=True))

        promedio_map = self._build_average_map(estudiante_ids, periodo_activo)
        asistencia_map = self._build_attendance_map(estudiante_ids)

        estudiantes = []
        for estudiante in queryset[offset : offset + page_size]:
            promedio = promedio_map.get(str(estudiante.id), 0)
            asistencia = asistencia_map.get(str(estudiante.id), 0)
            estudiantes.append(self._serialize_student(estudiante, promedio, asistencia))

        return {
            "resumen": self._build_summary(queryset, periodo_activo),
            "estudiantes": estudiantes,
            "paginacion": {
                "pagina": page,
                "tamano": page_size,
                "total": total_estudiantes,
                "paginas": max((total_estudiantes + page_size - 1) // page_size, 1),
                "siguiente": page * page_size < total_estudiantes,
                "anterior": page > 1,
            },
            "filtros": {
                "grados": self._build_grade_filters(),
                "periodo_activo": self._format_period(periodo_activo),
            },
            "permisos": self.access_service.build_permissions_payload(self._current_user),
        }

    def create_student(self, usuario, data):
        if not self.access_service.can_create_academic_data(usuario):
            raise PermissionError("No tienes permisos para crear estudiantes")

        nombres = (data.get("nombres") or "").strip()
        primer_apellido = (data.get("primer_apellido") or "").strip()
        segundo_apellido = (data.get("segundo_apellido") or "").strip() or None
        email = (data.get("email") or "").strip().lower()
        ci = (data.get("ci") or "").strip()
        telefono = (data.get("telefono") or "").strip() or None
        grado_id = data.get("grado_id")
        genero = (data.get("genero") or "").strip() or None
        estado = (data.get("estado") or "Activo").strip()
        password = (data.get("password") or ci or email).strip()

        if not nombres or not primer_apellido or not email or not ci or not grado_id:
            raise ValueError("Debes enviar nombres, primer apellido, email, ci y grado")

        try:
            grado = Grados.objects.get(id=grado_id)
        except Grados.DoesNotExist as exc:
            raise ValueError("El grado seleccionado no existe") from exc

        with transaction.atomic():
            if Usuarios.objects.filter(email__iexact=email).exists():
                raise ValueError("Ya existe un usuario con ese email")
            if Usuarios.objects.filter(ci__iexact=ci).exists():
                raise ValueError("Ya existe un usuario con ese CI")

            usuario_creado = Usuarios.objects.create(
                id=uuid4(),
                nombre=nombres,
                apellido=primer_apellido,
                email=email,
                password_hash=make_password(password),
                ci=ci,
                telefono=telefono,
                activo=True,
            )

            estudiante = Estudiantes.objects.create(
                id=uuid4(),
                usuario=usuario_creado,
                grado=grado,
                primer_apellido=primer_apellido,
                segundo_apellido=segundo_apellido,
                nombres=nombres,
                ci=ci,
                genero=genero,
                estado=estado,
                created_at=timezone.now(),
            )

            self._assign_student_role(usuario_creado, usuario)

        promedio = self._calculate_average_for_student(estudiante.id)
        asistencia = self._calculate_attendance_for_student(estudiante.id)
        return self._serialize_student(estudiante, promedio, asistencia)

    def _build_summary(self, queryset, periodo_activo):
        total_estudiantes = queryset.count()
        activos = queryset.filter(Q(estado__iexact="Activo") | Q(estado__isnull=True) | Q(estado="")).count()
        inactivos = total_estudiantes - activos

        estudiante_ids = list(queryset.values_list("id", flat=True))
        promedio_qs = Notas.objects.filter(estudiante_id__in=estudiante_ids, total__isnull=False)
        if periodo_activo is not None:
            promedio_qs = promedio_qs.filter(periodo=periodo_activo)
        promedio_general = promedio_qs.aggregate(promedio=Avg("total"))["promedio"] or 0

        asistencia_promedio = self._calculate_attendance_average(estudiante_ids)

        return [
            {
                "titulo": "Total Estudiantes",
                "valor": str(total_estudiantes),
                "detalle": "Listado general del sistema",
                "acento": "blue",
            },
            {
                "titulo": "Estudiantes Activos",
                "valor": str(activos),
                "detalle": f"{inactivos} inactivos o retirados",
                "acento": "green",
            },
            {
                "titulo": "Promedio General",
                "valor": f"{promedio_general:.1f}",
                "detalle": self._period_label(periodo_activo),
                "acento": "violet",
            },
            {
                "titulo": "Asistencia Promedio",
                "valor": f"{asistencia_promedio}%",
                "detalle": "Promedio de asistencia acumulada",
                "acento": "orange",
            },
        ]

    def _serialize_student(self, estudiante, promedio, asistencia):
        grado = estudiante.grado
        nombre = f"{estudiante.nombres} {estudiante.primer_apellido}".strip()
        if estudiante.segundo_apellido:
            nombre = f"{nombre} {estudiante.segundo_apellido}".strip()

        return {
            "id": str(estudiante.id),
            "nombre": nombre,
            "codigo": self._build_student_code(estudiante),
            "email": getattr(estudiante.usuario, "email", "") or "",
            "telefono": getattr(estudiante.usuario, "telefono", "") or "-",
            "grado": {
                "id": str(grado.id),
                "nombre": f"{grado.nivel} {grado.numero}{grado.paralelo}",
            },
            "promedio": round(float(promedio or 0), 1),
            "asistencia": asistencia,
            "estado": self._normalize_state(estudiante.estado),
            "estado_clase": "Activo" if self._is_active(estudiante.estado) else "Inactivo",
            "avatar": self._avatar_label(estudiante),
        }

    def _build_average_map(self, estudiante_ids, periodo_activo):
        if not estudiante_ids:
            return {}

        queryset = Notas.objects.filter(estudiante_id__in=estudiante_ids, total__isnull=False)
        if periodo_activo is not None:
            queryset = queryset.filter(periodo=periodo_activo)

        aggregation = queryset.values("estudiante_id").annotate(promedio=Avg("total"))
        return {str(item["estudiante_id"]): round(float(item["promedio"] or 0), 1) for item in aggregation}

    def _build_attendance_map(self, estudiante_ids):
        if not estudiante_ids:
            return {}

        queryset = Asistencias.objects.filter(estudiante_id__in=estudiante_ids)
        aggregation = queryset.values("estudiante_id").annotate(
            total=Count("id"),
            presentes=Count(
                "id",
                filter=~Q(estado__iexact="Falta") & ~Q(estado__iexact="Ausente") & ~Q(estado__iexact="Inasistencia"),
            ),
        )

        attendance_map = {}
        for item in aggregation:
            total = item["total"] or 0
            presentes = item["presentes"] or 0
            attendance_map[str(item["estudiante_id"])] = round((presentes / total) * 100) if total else 0
        return attendance_map

    def _calculate_attendance_average(self, estudiante_ids):
        attendance_map = self._build_attendance_map(estudiante_ids)
        if not attendance_map:
            return 0
        return round(sum(attendance_map.values()) / len(attendance_map))

    def _build_grade_filters(self):
        grades = Grados.objects.order_by("gestion", "nivel", "numero", "paralelo")
        if not self.access_service.can_view_all_academic_data(self._current_user):
            grade_ids = self.access_service.get_assigned_grade_ids(self._current_user)
            if grade_ids:
                grades = grades.filter(id__in=grade_ids)
            else:
                grades = grades.none()
        return [
            {
                "id": str(grado.id),
                "nombre": f"{grado.nivel} {grado.numero}{grado.paralelo}",
            }
            for grado in grades
        ]

    def _build_student_code(self, estudiante):
        if estudiante.ci:
            return estudiante.ci
        return str(estudiante.id).split("-")[0].upper()

    def _avatar_label(self, estudiante):
        initials = "".join(part[0] for part in [estudiante.nombres, estudiante.primer_apellido] if part).upper()
        return initials[:2] or "ES"

    def _normalize_state(self, estado):
        if not estado:
            return "Activo"
        return estado.strip().title()

    def _is_active(self, estado):
        if not estado:
            return True
        return estado.strip().lower() == "activo"

    def _get_periodo_activo(self):
        periodo = Periodos.objects.filter(activo=True).order_by("-gestion", "-numero").first()
        if periodo is not None:
            return periodo
        return Periodos.objects.order_by("-gestion", "-numero").first()

    def _period_label(self, periodo_activo):
        if periodo_activo is None:
            return "Promedio calculado con los registros disponibles"
        return f"{periodo_activo.nombre} {periodo_activo.gestion}"

    def _format_period(self, periodo_activo):
        if periodo_activo is None:
            return None
        return {
            "nombre": periodo_activo.nombre,
            "numero": periodo_activo.numero,
            "gestion": periodo_activo.gestion,
            "fecha_inicio": periodo_activo.fecha_inicio,
            "fecha_fin": periodo_activo.fecha_fin,
            "activo": bool(periodo_activo.activo),
        }

    def _calculate_average_for_student(self, estudiante_id):
        queryset = Notas.objects.filter(estudiante_id=estudiante_id, total__isnull=False)
        periodo_activo = self._get_periodo_activo()
        if periodo_activo is not None:
            queryset = queryset.filter(periodo=periodo_activo)
        return queryset.aggregate(promedio=Avg("total"))["promedio"] or 0

    def _calculate_attendance_for_student(self, estudiante_id):
        queryset = Asistencias.objects.filter(estudiante_id=estudiante_id)
        total = queryset.count()
        if not total:
            return 0

        presentes = queryset.exclude(estado__iexact="Falta").exclude(estado__iexact="Ausente").exclude(estado__iexact="Inasistencia").count()
        return round((presentes / total) * 100)

    def _assign_student_role(self, usuario_creado, assigned_by):
        role = Roles.objects.filter(nombre__iexact="estudiante").first()
        if role is None:
            return

        UsuarioRoles.objects.get_or_create(
            usuario=usuario_creado,
            rol=role,
            defaults={
                "asignado_por": assigned_by,
                "fecha_asignacion": timezone.now(),
                "activo": True,
            },
        )

    @property
    def _current_user(self):
        return getattr(self, "usuario", None)

