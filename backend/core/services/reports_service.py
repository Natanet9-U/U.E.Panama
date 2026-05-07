from collections import Counter

from django.db.models import Avg
from django.utils import timezone

from ..models import Asistencias, DocenteAsignacion, Estudiantes, Notas, Periodos
from .access_service import AccessControlService


class ReportsService:
    def __init__(self):
        self.access_service = AccessControlService()

    def build_reports_page(self, usuario, *, periodo_id=None):
        notes_queryset = Notas.objects.select_related(
            "estudiante__usuario",
            "asignacion__area",
            "asignacion__grado",
            "asignacion__docente__usuario",
            "periodo",
        ).order_by("-updated_at", "-created_at")
        notes_queryset = self.access_service.filter_notes_queryset(notes_queryset, usuario)
        if periodo_id:
            notes_queryset = notes_queryset.filter(periodo_id=periodo_id)
        notes = list(notes_queryset.filter(total__isnull=False))

        attendance_queryset = Asistencias.objects.select_related("estudiante__usuario", "estudiante__grado")
        attendance_queryset = self.access_service.filter_students_queryset(attendance_queryset, usuario)
        attendance = list(attendance_queryset)

        students_queryset = Estudiantes.objects.select_related("usuario", "grado")
        students_queryset = self.access_service.filter_students_queryset(students_queryset, usuario)

        summary = self._build_summary(notes, attendance, students_queryset.count())
        academic_report = self._build_academic_report(notes)
        attendance_report = self._build_attendance_report(attendance)
        risk_report = self._build_risk_report(notes)

        return {
            "resumen": summary,
            "reportes": [academic_report, attendance_report, risk_report],
            "top_estudiantes": self._build_top_students(notes),
            "alertas": self._build_alerts(notes, usuario),
            "cursos": self._build_courses(notes, usuario),
            "filtros": {
                "periodos": self._build_periods(),
            },
            "permisos": self.access_service.build_permissions_payload(usuario),
        }

    def _build_summary(self, notes, attendance, visible_students):
        graded_count = len(notes)
        average = sum(note.total for note in notes) / graded_count if graded_count else 0
        attendance_rate = self._attendance_rate(attendance)
        featured = sum(1 for note in notes if note.total >= 90)
        courses = self._visible_courses_count(notes)
        return [
            {"titulo": "Promedio General", "valor": f"{average:.1f}", "detalle": "Promedio de notas visibles", "acento": "blue"},
            {"titulo": "Asistencia", "valor": f"{attendance_rate}%", "detalle": "Asistencia acumulada", "acento": "green"},
            {"titulo": "Destacados", "valor": str(featured), "detalle": "Notas sobre 90", "acento": "violet"},
            {"titulo": "Cursos Visibles", "valor": str(courses), "detalle": f"{visible_students} estudiantes en alcance", "acento": "orange"},
        ]

    def _build_academic_report(self, notes):
        period_name = self._current_period_name(notes)
        averages = self._subject_averages(notes)
        return {
            "titulo": "Rendimiento Académico",
            "estado": "Generado",
            "periodo": period_name,
            "detalle": "Consolidado de rendimiento por asignatura",
            "labels": [item[0] for item in averages],
            "data": [item[1] for item in averages],
        }

    def _build_attendance_report(self, attendance):
        per_grade = Counter()
        for record in attendance:
            grade_label = f"{record.estudiante.grado.nivel} {record.estudiante.grado.numero}{record.estudiante.grado.paralelo}"
            per_grade[grade_label] += 1

        labels = list(per_grade.keys())
        data = list(per_grade.values())
        return {
            "titulo": "Asistencia por Grado",
            "estado": "Generado",
            "periodo": timezone.localdate().strftime("%B %Y"),
            "detalle": "Registro de asistencias acumuladas por curso",
            "labels": labels,
            "data": data,
        }

    def _build_risk_report(self, notes):
        low_performance = [note for note in notes if note.total < 70]
        return {
            "titulo": "Estudiantes en Riesgo",
            "estado": "Generado" if low_performance else "Sin incidencias",
            "periodo": self._current_period_name(notes),
            "detalle": "Estudiantes con promedio bajo requerirán seguimiento",
            "cantidad": len(low_performance),
            "porcentaje": self._percentage(len(low_performance), len(notes)),
        }

    def _build_top_students(self, notes):
        ranking = {}
        for note in notes:
            ranking.setdefault(note.estudiante_id, []).append(note.total)

        items = []
        for student_id, values in ranking.items():
            student = next((note.estudiante for note in notes if note.estudiante_id == student_id), None)
            if student is None:
                continue

            promedio = round(sum(values) / len(values), 1)
            items.append(
                {
                    "nombre": f"{student.nombres} {student.primer_apellido}".strip(),
                    "promedio": promedio,
                    "mensaje": "Excelente rendimiento" if promedio >= 90 else "Buen desempeño",
                }
            )

        return sorted(items, key=lambda item: item["promedio"], reverse=True)[:5]

    def _build_alerts(self, notes, usuario):
        alerts = []
        low_notes = [note for note in notes if note.total < 70]
        if low_notes:
            alerts.append(
                {
                    "titulo": "Seguimiento académico",
                    "detalle": f"Hay {len(low_notes)} calificaciones por debajo de 70 en el alcance visible.",
                    "tipo": "warning",
                }
            )

        pending_notes = Notas.objects.filter(total__isnull=True)
        pending_notes = self.access_service.filter_notes_queryset(pending_notes, usuario)
        if pending_notes.exists():
            alerts.append(
                {
                    "titulo": "Calificaciones pendientes",
                    "detalle": f"Existen {pending_notes.count()} calificaciones sin registrar.",
                    "tipo": "info",
                }
            )

        if not alerts:
            alerts.append({"titulo": "Sin alertas", "detalle": "No se detectaron incidencias en el alcance actual.", "tipo": "success"})

        return alerts

    def _build_courses(self, notes, usuario):
        assignment_ids = self.access_service.get_assigned_assignment_ids(usuario)
        queryset = DocenteAsignacion.objects.select_related("area", "grado", "docente__usuario")
        if not self.access_service.can_view_all_academic_data(usuario):
            queryset = queryset.filter(id__in=assignment_ids)

        courses = []
        for assignment in queryset:
            assignment_notes = [note for note in notes if note.asignacion_id == assignment.id]
            if not assignment_notes:
                continue

            average = round(sum(note.total for note in assignment_notes) / len(assignment_notes), 1)
            courses.append(
                {
                    "nombre": assignment.area.nombre,
                    "grado": f"{assignment.grado.nivel} {assignment.grado.numero}{assignment.grado.paralelo}",
                    "promedio": average,
                    "estudiantes": len({note.estudiante_id for note in assignment_notes}),
                }
            )

        return sorted(courses, key=lambda item: item["promedio"], reverse=True)[:6]

    def _subject_averages(self, notes):
        grouped = {}
        for note in notes:
            subject = note.asignacion.area.nombre
            grouped.setdefault(subject, []).append(note.total)

        return [(subject, round(sum(values) / len(values), 1)) for subject, values in grouped.items()]

    def _attendance_rate(self, attendance):
        if not attendance:
            return 0

        present = sum(1 for record in attendance if self._is_positive_state(record.estado))
        return round((present / len(attendance)) * 100)

    def _visible_courses_count(self, notes):
        return len({note.asignacion_id for note in notes})

    def _current_period_name(self, notes):
        if not notes:
            return "Sin periodo visible"

        period = notes[0].periodo
        return f"{period.nombre} {period.gestion}"

    def _build_periods(self):
        periods = Periodos.objects.order_by("-gestion", "-numero")
        return [{"id": str(period.id), "nombre": f"{period.nombre} {period.gestion}"} for period in periods]

    def _percentage(self, numerator, denominator):
        if not denominator:
            return 0
        return round((numerator / denominator) * 100)

    def _is_positive_state(self, estado):
        estado_normalizado = (estado or "").strip().lower()
        return estado_normalizado not in {"falta", "ausente", "inasistencia"}