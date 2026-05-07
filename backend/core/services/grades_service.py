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
