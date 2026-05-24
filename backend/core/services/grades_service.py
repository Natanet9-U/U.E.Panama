from collections import defaultdict

from django.db.models import Q

from ..models import Notas, Periodos
from .access_service import AccessControlService


class GradesService:
    def __init__(self):
        self.access_service = AccessControlService()

    def build_grades_page(self, usuario, *, query=None, periodo_id=None, page=1, page_size=10):
        queryset = (
            Notas.objects.select_related(
                "estudiante__usuario",
                "asignacion__area",
                "asignacion__grado",
                "asignacion__docente__usuario",
                "periodo",
            )
            .order_by("-updated_at", "-created_at")
        )
        queryset = self.access_service.filter_notes_queryset(queryset, usuario)

        if query:
            queryset = queryset.filter(
                Q(estudiante__nombres__icontains=query)
                | Q(estudiante__primer_apellido__icontains=query)
                | Q(asignacion__area__nombre__icontains=query)
                | Q(asignacion__grado__nivel__icontains=query)
                | Q(periodo__nombre__icontains=query)
            )

        if periodo_id:
            queryset = queryset.filter(periodo_id=periodo_id)

        notes = list(queryset)
        subject_names = self._collect_subject_names(notes)
        student_groups = self._group_by_student(notes)
        course_groups = self._group_by_course(notes)

        total = len(notes)
        page = max(int(page or 1), 1)
        page_size = max(min(int(page_size or 10), 50), 1)
        offset = (page - 1) * page_size

        return {
            "resumen": self._build_summary(notes),
            "promedio_por_asignatura": self._build_subject_chart(notes, subject_names),
            "mejores_estudiantes": self._build_student_ranking(student_groups),
            "por_estudiante": self._build_students_view(student_groups, subject_names),
            "por_curso": self._build_courses_view(course_groups),
            "calificaciones": [self._serialize_grade(item) for item in notes[offset : offset + page_size]],
            "paginacion": {
                "pagina": page,
                "tamano": page_size,
                "total": total,
                "paginas": max((total + page_size - 1) // page_size, 1),
                "siguiente": page * page_size < total,
                "anterior": page > 1,
            },
            "filtros": {
                "periodos": self._build_periods(),
                "materias": subject_names,
            },
            "permisos": self.access_service.build_permissions_payload(usuario),
        }

    def _build_summary(self, notes):
        graded_notes = [note for note in notes if note.total is not None]
        total = len(notes)
        promedio = sum(note.total for note in graded_notes) / len(graded_notes) if graded_notes else 0
        aprobadas = sum(1 for note in graded_notes if note.total >= 70)
        en_riesgo = sum(1 for note in graded_notes if 60 <= note.total < 70)
        destacados = sum(1 for note in graded_notes if note.total >= 90)
        return [
            {"titulo": "Promedio General", "valor": f"{promedio:.1f}", "detalle": "Rendimiento global", "acento": "blue"},
            {"titulo": "Aprobados", "valor": f"{self._percentage(aprobadas, len(graded_notes))} %", "detalle": "Notas sobre 70", "acento": "green"},
            {"titulo": "En Riesgo", "valor": str(en_riesgo), "detalle": "Entre 60 y 69", "acento": "orange"},
            {"titulo": "Destacados", "valor": str(destacados), "detalle": "Notas sobre 90", "acento": "violet"},
        ]

    def _build_subject_chart(self, notes, subject_names):
        averages = []
        labels = []
        for subject_name in subject_names:
            subject_notes = [note.total for note in notes if note.total is not None and note.asignacion.area.nombre == subject_name]
            labels.append(subject_name)
            averages.append(round(sum(subject_notes) / len(subject_notes), 1) if subject_notes else 0)

        return {"labels": labels, "data": averages}

    def _build_student_ranking(self, student_groups):
        ranking = []
        for student_id, group in student_groups.items():
            graded_notes = [note for note in group["notes"] if note.total is not None]
            if not graded_notes:
                continue

            average = sum(note.total for note in graded_notes) / len(graded_notes)
            ranking.append({
                "id": str(student_id),
                "nombre": group["nombre"],
                "documento": group["documento"],
                "promedio": round(average, 1),
                "detalle": self._student_badge(average),
            })

        ranking.sort(key=lambda item: item["promedio"], reverse=True)
        for index, item in enumerate(ranking, start=1):
            item["posicion"] = index
        return ranking[:5]

    def _build_students_view(self, student_groups, subject_names):
        rows = []
        for student_id, group in student_groups.items():
            subject_totals = {subject_name: "-" for subject_name in subject_names}
            graded_notes = [note for note in group["notes"] if note.total is not None]
            for note in graded_notes:
                subject_totals[note.asignacion.area.nombre] = note.total

            average = sum(note.total for note in graded_notes) / len(graded_notes) if graded_notes else 0
            rows.append({
                "id": str(student_id),
                "estudiante": group["nombre"],
                "documento": group["documento"],
                "materias": subject_totals,
                "promedio": round(average, 1),
                "tendencia": self._trend_for_average(average),
            })

        rows.sort(key=lambda item: item["promedio"], reverse=True)
        return rows

    def _build_courses_view(self, course_groups):
        cards = []
        for course_id, group in course_groups.items():
            graded_notes = [note for note in group["notes"] if note.total is not None]
            if not graded_notes:
                continue

            average = sum(note.total for note in graded_notes) / len(graded_notes)
            cards.append({
                "id": str(course_id),
                "curso": group["nombre"],
                "promedio": round(average, 1),
                "estudiantes": len({note.estudiante_id for note in graded_notes}),
                "distribucion": self._build_distribution(graded_notes),
                "mejor_estudiante": self._best_student_name(graded_notes),
            })

        cards.sort(key=lambda item: item["promedio"], reverse=True)
        return cards

    def _collect_subject_names(self, notes):
        seen = set()
        names = []
        for note in notes:
            subject_name = note.asignacion.area.nombre
            if subject_name not in seen:
                seen.add(subject_name)
                names.append(subject_name)

        return names

    def _group_by_student(self, notes):
        groups = {}
        for note in notes:
            student = note.estudiante
            group = groups.setdefault(student.id, {
                "nombre": f"{student.nombres} {student.primer_apellido}".strip(),
                "documento": student.ci or str(student.id)[:4].upper(),
                "notes": [],
            })
            group["notes"].append(note)
        return groups

    def _group_by_course(self, notes):
        groups = {}
        for note in notes:
            course = note.asignacion.area
            group = groups.setdefault(course.id, {
                "nombre": course.nombre,
                "notes": [],
            })
            group["notes"].append(note)
        return groups

    def _build_distribution(self, notes):
        total = len(notes) or 1
        ranges = [
            ("Calificaciones 90+", lambda value: value >= 90, "#dcfce7"),
            ("Calificaciones 80-89", lambda value: 80 <= value < 90, "#dbeafe"),
            ("Calificaciones 70-79", lambda value: 70 <= value < 80, "#ffedd5"),
            ("Calificaciones <70", lambda value: value < 70, "#fee2e2"),
        ]

        distribution = []
        for label, matcher, color in ranges:
            count = sum(1 for note in notes if note.total is not None and matcher(note.total))
            distribution.append({"label": label, "value": round((count / total) * 100), "color": color})
        return distribution

    def _best_student_name(self, notes):
        grouped = defaultdict(list)
        for note in notes:
            grouped[note.estudiante_id].append(note)

        best_student = None
        best_average = -1
        for student_id, student_notes in grouped.items():
            average = sum(note.total for note in student_notes if note.total is not None) / len(student_notes)
            if average > best_average:
                best_average = average
                best_student = student_notes[0].estudiante

        if best_student is None:
            return "-"

        return f"{best_student.nombres} {best_student.primer_apellido}".strip()

    def _trend_for_average(self, average):
        if average >= 85:
            return "up"
        if average >= 70:
            return "stable"
        return "down"

    def _student_badge(self, average):
        if average >= 90:
            return "Excelente"
        if average >= 80:
            return "Bueno"
        if average >= 70:
            return "En progreso"
        return "Requiere apoyo"

    def _percentage(self, numerator, denominator):
        if not denominator:
            return 0
        return round((numerator / denominator) * 100)

    def _serialize_grade(self, nota):
        estudiante = nota.estudiante
        asignacion = nota.asignacion
        docente = asignacion.docente.usuario
        return {
            "id": str(nota.id),
            "estudiante": f"{estudiante.nombres} {estudiante.primer_apellido}".strip(),
            "grado": f"{asignacion.grado.nivel} {asignacion.grado.numero}{asignacion.grado.paralelo}",
            "curso": asignacion.area.nombre,
            "docente": f"{docente.nombre} {docente.apellido}".strip(),
            "periodo": nota.periodo.nombre,
            "total": nota.total,
            "indicador": nota.indicador or "-",
            "observaciones": nota.observaciones or "-",
            "actualizado": nota.updated_at or nota.created_at,
        }

    def _build_periods(self):
        periods = Periodos.objects.order_by("-gestion", "-numero")
        return [{"id": str(period.id), "nombre": f"{period.nombre} {period.gestion}"} for period in periods]

    def update_student_grades(self, usuario, asignacion_id, periodo_id, payload):
        """
        payload: list of { estudiante_id, detalles: [ { dimension_id, valor } ], indicador?, observaciones? }
        Only teachers assigned to the assignment or direct roles can update.
        Calculates Nota.total as the average percentage across dimensiones (valor / puntaje_maximo * 100).
        """
        if not self.access_service.can_view_all_academic_data(usuario):
            # ensure teacher is owner of assignment
            assigned_ids = self.access_service.get_assigned_assignment_ids(usuario)
            if asignacion_id not in assigned_ids:
                raise PermissionError("No tienes permisos para modificar notas en esta asignación")

        # lazy import models
        from ..models import Notas, NotaDetalle, DimensionesEvaluacion
        updated = []
        dimensiones_map = {d.id: d for d in DimensionesEvaluacion.objects.filter(activo=True)}

        for item in payload or []:
            estudiante_id = item.get("estudiante_id")
            detalles = item.get("detalles") or []
            indicador = item.get("indicador")
            observaciones = item.get("observaciones")

            nota_obj, created = Notas.objects.get_or_create(
                estudiante_id=estudiante_id,
                asignacion_id=asignacion_id,
                periodo_id=periodo_id,
                defaults={"id": None},
            )

            # ensure id if None
            if nota_obj.id is None:
                from uuid import uuid4
                nota_obj.id = uuid4()

            # save/replace detalle values
            for det in detalles:
                dim_id = det.get("dimension_id")
                valor = det.get("valor")
                if dim_id is None or valor is None:
                    continue

                dim = dimensiones_map.get(dim_id)
                if dim is None:
                    try:
                        dim = DimensionesEvaluacion.objects.get(id=dim_id)
                        dimensiones_map[dim.id] = dim
                    except DimensionesEvaluacion.DoesNotExist:
                        continue

                nd, _ = NotaDetalle.objects.update_or_create(
                    nota=nota_obj,
                    dimension=dim,
                    defaults={"valor": int(valor)},
                )

                try:
                    dim_value = int(valor)
                except Exception:
                    dim_value = 0

                if dim.puntaje_maximo:
                    dim_value = max(0, min(dim_value, int(dim.puntaje_maximo)))

            # compute nota total from all active dimension details currently stored for the note
            nota_total = sum(
                int(detalle.valor or 0)
                for detalle in NotaDetalle.objects.filter(nota=nota_obj, dimension__activo=True).select_related("dimension")
            )
            if nota_total == 0 and not NotaDetalle.objects.filter(nota=nota_obj).exists():
                nota_total = None

            nota_obj.total = nota_total
            nota_obj.indicador = indicador or nota_obj.indicador
            nota_obj.observaciones = observaciones or nota_obj.observaciones
            from django.utils import timezone
            nota_obj.updated_at = timezone.now()
            nota_obj.save()

            updated.append({"estudiante_id": str(estudiante_id), "nota_total": nota_total})

        return updated

    def compute_trimestral_and_overall(self, asignacion_id):
        """
        For an assignment, compute per-student totals per periodo (trimestre), per-dimension percentages per periodo,
        and overall final as average of available period totals.
        Returns list of { estudiante_id, por_periodo: {numero: total}, dimensiones: {numero: {dimension_id: promedio_pct}}, final }
        """
        from ..models import Notas, NotaDetalle, Periodos

        # collect period numbers for this gestion
        periodos = list(Periodos.objects.order_by('numero'))
        periodo_map = {str(p.id): p for p in periodos}

        notas_qs = Notas.objects.filter(asignacion_id=asignacion_id).select_related('estudiante', 'periodo')
        students = {}

        for nota in notas_qs:
            est_id = str(nota.estudiante_id)
            student = students.setdefault(est_id, {"nombre": f"{nota.estudiante.nombres} {nota.estudiante.primer_apellido}", "por_periodo": {}, "dimensiones": {}})
            periodo_num = nota.periodo.numero if hasattr(nota, 'periodo') and nota.periodo else None
            if periodo_num is not None:
                student["por_periodo"][periodo_num] = nota.total

            # accumulate dimensiones for this nota
            for nd in NotaDetalle.objects.filter(nota=nota).select_related('dimension'):
                num = nota.periodo.numero if nota.periodo else None
                if num is None:
                    continue
                dim_map = student["dimensiones"].setdefault(num, {})
                lst = dim_map.setdefault(str(nd.dimension_id), [])
                try:
                    pct = (nd.valor / float(nd.dimension.puntaje_maximo)) * 100 if nd.dimension.puntaje_maximo else 0
                except Exception:
                    pct = 0
                lst.append(pct)

        results = []
        for est_id, info in students.items():
            por_periodo = info.get("por_periodo", {})
            dimensiones_out = {}
            for periodo_num, dims in info.get("dimensiones", {}).items():
                dimensiones_out[periodo_num] = {dim_id: int(round(sum(vals) / len(vals))) if vals else None for dim_id, vals in dims.items()}

            # compute overall final as average of available period totals
            totals = [v for v in por_periodo.values() if v is not None]
            final = int(round(sum(totals) / len(totals))) if totals else None

            results.append({"estudiante_id": est_id, "nombre": info.get("nombre"), "por_periodo": por_periodo, "dimensiones": dimensiones_out, "final": final})

        return results

    def get_activities_average(self, asignacion_id):
        """
        For an assignment, calculate average grade per student from ActividadNota records.
        Returns dict: { estudiante_id: average_score (0-100 scale) }
        """
        from ..models import ActividadNotas, Actividades

        activities_avg = {}
        estudiantes_notas = {}

        # collect all activity grades for this assignment
        actividades = Actividades.objects.filter(asignacion_id=asignacion_id)
        for actividad in actividades:
            notas = ActividadNotas.objects.filter(actividad=actividad)
            for nota in notas:
                est_id = str(nota.estudiante_id)
                # normalize nota to 100-scale based on actividad.puntaje_maximo
                normalized = (nota.valor / float(actividad.puntaje_maximo)) * 100 if actividad.puntaje_maximo else 0
                if est_id not in estudiantes_notas:
                    estudiantes_notas[est_id] = []
                estudiantes_notas[est_id].append(normalized)

        # compute average per student
        for est_id, notas_list in estudiantes_notas.items():
            if notas_list:
                activities_avg[est_id] = int(round(sum(notas_list) / len(notas_list)))
            else:
                activities_avg[est_id] = 0

        return activities_avg

    def recompute_from_actividades(self, usuario, asignacion_id, periodo_id):
        """
        Recomputes Notas and NotaDetalle for a given assignment and periodo based on Actividades and ActividadNotas.
        Activities that have `dimension` are aggregated per-dimension; activities without a dimension contribute as a general component.
        The final Nota.total is the average of all dimension percentages plus the general percentage (if present).
        """
        if not self.access_service.can_view_all_academic_data(usuario):
            assigned_ids = self.access_service.get_assigned_assignment_ids(usuario)
            if asignacion_id not in assigned_ids:
                raise PermissionError("No tienes permisos para recomputar notas en esta asignación")

        from ..models import Actividades, ActividadNotas, Notas, NotaDetalle, DimensionesEvaluacion, Estudiantes, DocenteAsignacion
        from uuid import uuid4
        from django.utils import timezone

        periodo = Periodos.objects.filter(id=periodo_id).first()
        if not periodo:
            raise ValueError("Periodo no encontrado")

        # determine students in the assignment's grado
        grado_id = DocenteAsignacion.objects.filter(id=asignacion_id).values_list('grado_id', flat=True).first()
        if not grado_id:
            raise ValueError("Asignacion no encontrada")

        estudiantes = Estudiantes.objects.filter(grado_id=grado_id)
        updated = []

        actividades_qs = Actividades.objects.filter(asignacion_id=asignacion_id)
        if periodo.fecha_inicio and periodo.fecha_fin:
            actividades_qs = actividades_qs.filter(fecha__range=(periodo.fecha_inicio, periodo.fecha_fin))
        actividades_qs = list(actividades_qs.select_related("dimension"))

        dimensiones = list(DimensionesEvaluacion.objects.filter(gestion=periodo.gestion, activo=True).order_by("orden"))
        auto_dimension = next((d for d in dimensiones if self._is_autoevaluacion_dimension(d.nombre)), None)
        dimensiones_normales = [d for d in dimensiones if not self._is_autoevaluacion_dimension(d.nombre)]

        # All activities contribute only to Nota.total (do not modify NotaDetalle)
        for s in estudiantes:
            an_qs = (
                ActividadNotas.objects.filter(actividad__in=actividades_qs, estudiante_id=s.id)
                .select_related("actividad", "actividad__dimension")
            )

            scores_by_dimension = {}
            for an in an_qs:
                act = an.actividad
                dimension = getattr(act, "dimension", None)
                if dimension is None or self._is_autoevaluacion_dimension(dimension.nombre):
                    continue

                if not act.puntaje_maximo:
                    continue

                normalized = (int(an.valor or 0) / float(act.puntaje_maximo)) * 100
                scores_by_dimension.setdefault(dimension.id, []).append(normalized)

            nota_obj, created = Notas.objects.get_or_create(
                estudiante_id=s.id,
                asignacion_id=asignacion_id,
                periodo_id=periodo_id,
                defaults={"id": uuid4(), "created_at": timezone.now()},
            )

            detalle_values = {}
            for dimension in dimensiones_normales:
                valores = scores_by_dimension.get(dimension.id, [])
                if valores:
                    detalle_values[dimension.id] = int(round((sum(valores) / len(valores)) * (dimension.puntaje_maximo / 100.0)))

            if auto_dimension is not None:
                auto_detalle = NotaDetalle.objects.filter(nota=nota_obj, dimension=auto_dimension).first()
                if auto_detalle is not None:
                    detalle_values[auto_dimension.id] = int(auto_detalle.valor or 0)
                else:
                    detalle_values[auto_dimension.id] = 0

            for dimension in dimensiones:
                if dimension.id not in detalle_values:
                    continue
                NotaDetalle.objects.update_or_create(
                    nota=nota_obj,
                    dimension=dimension,
                    defaults={"valor": max(0, min(int(detalle_values[dimension.id]), int(dimension.puntaje_maximo)))},
                )

            nota_total = sum(int(value) for value in detalle_values.values()) if detalle_values else None
            nota_obj.total = nota_total
            nota_obj.updated_at = timezone.now()
            nota_obj.save()

            updated.append({"estudiante_id": str(s.id), "nota_total": nota_total})

        return updated

    def _is_autoevaluacion_dimension(self, nombre):
        normalized = (nombre or "").strip().lower()
        normalized = normalized.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        return normalized.startswith("autoevalu")
