"""Tests para GradesService"""
from types import SimpleNamespace
from uuid import uuid4

import pytest

from core.models import Areas, DocenteAsignacion, Docentes, Estudiantes, Grados, Notas, Periodos
from core.services.grades_service import GradesService
from core.tests.factories.user_factory import UsuarioFactory


@pytest.mark.django_db
class TestGradesService:
    """Tests para el servicio de calificaciones"""

    def setup_method(self):
        """Configuración antes de cada test"""
        self.service = GradesService()

    def test_placeholder(self):
        """Placeholder para tests de calificaciones"""
        pass

    def test_build_grades_page_summary(self):
        from django.utils import timezone

        usuario = UsuarioFactory()
        periodo = Periodos.objects.create(id=uuid4(), nombre="P1", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31", activo=True)
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Historia")
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)

        est_user = UsuarioFactory()
        estudiante = Estudiantes.objects.create(id=uuid4(), usuario=est_user, grado=grado, primer_apellido="Z", nombres="Ana", ci="CI3")
        Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo, total=95, created_at=timezone.now())

        service = GradesService()
        res = service.build_grades_page(usuario)
        assert "resumen" in res
        assert isinstance(res["resumen"], list)

    def test_helper_methods(self):
        assignment = SimpleNamespace(area=SimpleNamespace(nombre="Historia", id=uuid4()), grado=SimpleNamespace(nivel="Primaria", numero=1, paralelo="A"), docente=SimpleNamespace(usuario=SimpleNamespace(nombre="Ana", apellido="Perez")))
        student = SimpleNamespace(nombres="Luis", primer_apellido="Gomez", ci="CI1", id=uuid4())
        note = SimpleNamespace(total=92, asignacion=assignment, estudiante=student, estudiante_id=student.id)

        assert self.service._percentage(2, 4) == 50
        assert self.service._percentage(0, 0) == 0
        assert self.service._trend_for_average(90) == "up"
        assert self.service._trend_for_average(75) == "stable"
        assert self.service._trend_for_average(60) == "down"
        assert self.service._student_badge(95) == "Excelente"
        assert self.service._student_badge(85) == "Bueno"
        assert self.service._student_badge(72) == "En progreso"
        assert self.service._student_badge(40) == "Requiere apoyo"

        distribution = self.service._build_distribution([note, SimpleNamespace(total=68), SimpleNamespace(total=81), SimpleNamespace(total=95)])
        assert distribution[0]["label"] == "Calificaciones 90+"
        assert self.service._best_student_name([note]) == "Luis Gomez"

        grouped = {student.id: {"nombre": "Luis Gomez", "documento": "CI1", "notes": [note]}}
        rows = self.service._build_students_view(grouped, ["Historia"])
        assert rows[0]["tendencia"] == "up"
        assert rows[0]["materias"]["Historia"] == 92

        courses = self.service._build_courses_view({assignment.area.id: {"nombre": "Historia", "notes": [note]}})
        assert courses[0]["curso"] == "Historia"
        assert courses[0]["mejor_estudiante"] == "Luis Gomez"

        notes = [SimpleNamespace(asignacion=assignment, estudiante=student, estudiante_id=student.id, total=90)]
        assert self.service._collect_subject_names(notes) == ["Historia"]
        assert self.service._group_by_student(notes)[student.id]["nombre"] == "Luis Gomez"
        assert self.service._group_by_course(notes)[assignment.area.id]["nombre"] == "Historia"

    def test_serialize_grade_and_periods(self):
        periodo = Periodos.objects.create(id=uuid4(), nombre="P1", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31", activo=True)
        area = Areas.objects.create(id=uuid4(), nombre="Matematica")
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
        estudiante = Estudiantes.objects.create(id=uuid4(), usuario=UsuarioFactory(), grado=grado, primer_apellido="Perez", nombres="Ana", ci="CI9")
        nota = Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo, total=88, indicador="OK", observaciones="Bien")

        serialized = self.service._serialize_grade(nota)
        assert serialized["curso"] == "Matematica"
        assert serialized["docente"] == f"{docente_user.nombre} {docente_user.apellido}".strip()
        assert serialized["periodo"] == "P1"

        periods = self.service._build_periods()
        assert any(period["nombre"].startswith("P1") for period in periods)


# Agrega tests específicos para el servicio de calificaciones
