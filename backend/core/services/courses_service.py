from uuid import uuid4
from datetime import time

from django.db import transaction
from django.db.models import Avg, Q

from ..models import Areas, DocenteAsignacion, Docentes, Estudiantes, Notas, Periodos, Grados, Horarios
from .access_service import AccessControlService


class CoursesService:
    def __init__(self):
        self.access_service = AccessControlService()

    def build_courses_page(self, usuario, *, query=None, page=1, page_size=6):
        queryset = (
            DocenteAsignacion.objects.select_related("docente__usuario", "grado", "area")
            .order_by("area__nombre", "grado__gestion", "grado__nivel", "grado__numero", "grado__paralelo")
        )
        queryset = self.access_service.filter_courses_queryset(queryset, usuario)

        if query:
            queryset = queryset.filter(
                Q(area__nombre__icontains=query)
                | Q(grado__nivel__icontains=query)
                | Q(grado__paralelo__icontains=query)
                | Q(docente__usuario__nombre__icontains=query)
                | Q(docente__usuario__apellido__icontains=query)
            )

        total_cursos = queryset.count()
        page = max(int(page or 1), 1)
        page_size = max(min(int(page_size or 6), 24), 1)
        offset = (page - 1) * page_size

        periodo_activo = self._get_periodo_activo()
        assignment_ids = list(queryset.values_list("id", flat=True))
        promedio_map = self._build_average_map(assignment_ids, periodo_activo)

        cursos = []
        for asignacion in queryset[offset : offset + page_size]:
            cursos.append(self._serialize_course(asignacion, promedio_map.get(str(asignacion.id), 0)))

        return {
            "resumen": self._build_summary(queryset, periodo_activo),
            "cursos": cursos,
            "paginacion": {
                "pagina": page,
                "tamano": page_size,
                "total": total_cursos,
                "paginas": max((total_cursos + page_size - 1) // page_size, 1),
                "siguiente": page * page_size < total_cursos,
                "anterior": page > 1,
            },
            "permisos": self.access_service.build_permissions_payload(usuario),
            "catalogos": self._build_catalogs(usuario),
        }

    def create_course(self, usuario, data):
        """
        Create a new course (DocenteAsignacion) with optional area/grade creation.
        
        Args:
            usuario: Authenticated user
            data: dict with:
                - area_name: str (required, will create if not found)
                - grado_nivel: str (required if creating grade)
                - grado_numero: int (required if creating grade)
                - grado_paralelo: str (required if creating grade)
                - grado_gestion: int (required if creating grade)
                - docente_id: str (required, must exist)
                - horarios: list of {dia_semana, hora_inicio, hora_fin, aula} (optional)
        
        Returns:
            dict with created course data
        """
        if not self.access_service.can_create_academic_data(usuario):
            raise PermissionError("No tienes permisos para crear cursos")

        area_name = data.get("area_name", "").strip()
        grado_id = data.get("grado_id")
        docente_id = data.get("docente_id")
        horarios_data = data.get("horarios", [])

        if not area_name or not docente_id:
            raise ValueError("Debes enviar area_name y docente_id")

        try:
            docente = Docentes.objects.get(id=docente_id)
        except Docentes.DoesNotExist as exc:
            raise ValueError("El docente seleccionado no existe") from exc

        # Get or create area
        area, _ = Areas.objects.get_or_create(nombre=area_name)

        # Get or create grade
        if not grado_id:
            grado_nivel = data.get("grado_nivel", "").strip()
            grado_numero = data.get("grado_numero")
            grado_paralelo = data.get("grado_paralelo", "").strip()
            grado_gestion = data.get("grado_gestion", 2026)

            if not grado_nivel or grado_numero is None or not grado_paralelo:
                raise ValueError("Debes enviar grado_nivel, grado_numero y grado_paralelo para crear un grado")

            grado, _ = Grados.objects.get_or_create(
                nivel=grado_nivel,
                numero=grado_numero,
                paralelo=grado_paralelo,
                gestion=grado_gestion,
            )
        else:
            try:
                grado = Grados.objects.get(id=grado_id)
            except Grados.DoesNotExist as exc:
                raise ValueError("El grado seleccionado no existe") from exc

        # Check if assignment already exists
        if DocenteAsignacion.objects.filter(docente=docente, grado=grado, area=area).exists():
            raise ValueError("Ese curso ya existe")

        with transaction.atomic():
            asignacion = DocenteAsignacion.objects.create(
                id=uuid4(),
                docente=docente,
                grado=grado,
                area=area,
            )

            # Create schedules if provided
            if horarios_data:
                self._create_schedules(asignacion, horarios_data)

        promedio = self._build_average_map([asignacion.id], self._get_periodo_activo()).get(str(asignacion.id), 0)
        return self._serialize_course(asignacion, promedio)

    def _create_schedules(self, asignacion, horarios_data):
        """Create schedule rows for a course assignment."""
        for horario_data in horarios_data:
            try:
                dia_semana = int(horario_data.get("dia_semana"))
                hora_inicio_str = horario_data.get("hora_inicio")
                hora_fin_str = horario_data.get("hora_fin")
                aula = horario_data.get("aula", "").strip()

                # Parse time strings (expected format: "HH:MM")
                hora_inicio = time.fromisoformat(hora_inicio_str) if isinstance(hora_inicio_str, str) else hora_inicio_str
                hora_fin = time.fromisoformat(hora_fin_str) if isinstance(hora_fin_str, str) else hora_fin_str

                Horarios.objects.get_or_create(
                    asignacion=asignacion,
                    dia_semana=dia_semana,
                    hora_inicio=hora_inicio,
                    defaults={
                        "id": uuid4(),
                        "hora_fin": hora_fin,
                        "aula": aula,
                    },
                )
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Datos de horario inválidos: {horario_data}") from exc

    def _build_summary(self, queryset, periodo_activo):
        total_cursos = queryset.count()
        total_estudiantes = self._count_students(queryset)
        promedio_general = self._calculate_average(queryset, periodo_activo)
        asignaciones_docentes = queryset.values("docente_id").distinct().count()

        return [
            {
                "titulo": "Cursos Activos",
                "valor": str(total_cursos),
                "detalle": "Asignaciones académicas visibles",
                "acento": "blue",
            },
            {
                "titulo": "Total Estudiantes",
                "valor": str(total_estudiantes),
                "detalle": "Estudiantes vinculados a estos cursos",
                "acento": "violet",
            },
            {
                "titulo": "Promedio General",
                "valor": f"{promedio_general:.1f}",
                "detalle": self._period_label(periodo_activo),
                "acento": "green",
            },
            {
                "titulo": "Docentes Asignados",
                "valor": str(asignaciones_docentes),
                "detalle": "Profesores con cursos activos",
                "acento": "orange",
            },
        ]

    def _serialize_course(self, asignacion, promedio):
        estudiantes = Estudiantes.objects.filter(grado_id=asignacion.grado_id).count()
        docente = asignacion.docente.usuario
        return {
            "id": str(asignacion.id),
            "codigo": self._build_course_code(asignacion),
            "nombre": asignacion.area.nombre,
            "docente": f"{docente.nombre} {docente.apellido}".strip(),
            "grado": f"{asignacion.grado.nivel} {asignacion.grado.numero}{asignacion.grado.paralelo}",
            "estudiantes": estudiantes,
            "promedio": round(float(promedio or 0), 1),
            "progreso": self._build_progress(estudiantes, promedio),
            "estado": "Completo" if estudiantes >= 30 else "Activo",
            "periodo": f"{asignacion.grado.gestion}",
        }

    def _build_average_map(self, assignment_ids, periodo_activo):
        if not assignment_ids:
            return {}

        queryset = Notas.objects.filter(asignacion_id__in=assignment_ids, total__isnull=False)
        if periodo_activo is not None:
            queryset = queryset.filter(periodo=periodo_activo)

        aggregation = queryset.values("asignacion_id").annotate(promedio=Avg("total"))
        return {str(item["asignacion_id"]): round(float(item["promedio"] or 0), 1) for item in aggregation}

    def _calculate_average(self, queryset, periodo_activo):
        assignment_ids = list(queryset.values_list("id", flat=True))
        if not assignment_ids:
            return 0

        notes = Notas.objects.filter(asignacion_id__in=assignment_ids, total__isnull=False)
        if periodo_activo is not None:
            notes = notes.filter(periodo=periodo_activo)

        return notes.aggregate(promedio=Avg("total"))["promedio"] or 0

    def _count_students(self, queryset):
        grade_ids = queryset.values_list("grado_id", flat=True).distinct()
        return Estudiantes.objects.filter(grado_id__in=grade_ids).count()

    def _build_progress(self, students_count, promedio):
        scaled_average = min(float(promedio or 0), 100)
        load_ratio = min((students_count / 30) * 100, 100) if students_count else 0
        return round((scaled_average + load_ratio) / 2)

    def _build_course_code(self, asignacion):
        area_code = "".join(part[0] for part in asignacion.area.nombre.split() if part)[:3].upper() or "CUR"
        return f"{area_code}{asignacion.grado.numero}{asignacion.grado.paralelo}"

    def _get_periodo_activo(self):
        periodo = Periodos.objects.filter(activo=True).order_by("-gestion", "-numero").first()
        if periodo is not None:
            return periodo
        return Periodos.objects.order_by("-gestion", "-numero").first()

    def _period_label(self, periodo_activo):
        if periodo_activo is None:
            return "Promedio calculado con los registros disponibles"
        return f"{periodo_activo.nombre} {periodo_activo.gestion}"

    def _build_catalogs(self, usuario):
        if not self.access_service.can_create_academic_data(usuario):
            return {"areas": [], "grados": [], "docentes": []}

        return {
            "areas": [{"id": str(area.id), "nombre": area.nombre} for area in Areas.objects.order_by("nombre")],
            "grados": [
                {"id": str(grado.id), "nombre": f"{grado.nivel} {grado.numero}{grado.paralelo}"}
                for grado in Grados.objects.order_by("gestion", "nivel", "numero", "paralelo")
            ],
            "docentes": [
                {"id": str(docente.id), "nombre": f"{docente.usuario.nombre} {docente.usuario.apellido}".strip()}
                for docente in Docentes.objects.select_related("usuario").order_by("usuario__apellido", "usuario__nombre")
            ],
        }
