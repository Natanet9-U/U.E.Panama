"""Tests para ReportsService"""
from types import SimpleNamespace
from uuid import uuid4

import pytest

from core.models import Areas, Asistencias, DocenteAsignacion, Docentes, Estudiantes, Grados, Notas, Periodos
from core.services.reports_service import ReportsService
from core.tests.factories.user_factory import UsuarioFactory


@pytest.mark.django_db
class TestReportsService:
    """Tests para el servicio de reportes"""

    def setup_method(self):
        """Configuración antes de cada test"""
        self.service = ReportsService()

    def test_placeholder(self):
        """Placeholder para tests de reportes"""
        pass

    def test_build_reports_page_alerts_and_top_students(self):
        from django.utils import timezone

        usuario = UsuarioFactory()
        periodo = Periodos.objects.create(id=uuid4(), nombre="P1", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31", activo=True)
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Biologia")
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)

        est_user = UsuarioFactory()
        estudiante = Estudiantes.objects.create(id=uuid4(), usuario=est_user, grado=grado, primer_apellido="M", nombres="Luis", ci="CI4")
        # low note to trigger risk
        Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo, total=55)
        # attendance
        Asistencias.objects.create(id=uuid4(), estudiante=estudiante, registrado_por=usuario, fecha=timezone.localdate(), estado="Presente")

        service = ReportsService()
        res = service.build_reports_page(usuario)
        assert "alertas" in res
        assert isinstance(res["top_estudiantes"], list)

    def test_helper_methods(self):
        assignment = SimpleNamespace(area=SimpleNamespace(nombre="Biologia"), grado=SimpleNamespace(nivel="Primaria", numero=2, paralelo="B"), id="course-1")
        period = SimpleNamespace(nombre="P1", gestion=2026)
        student = SimpleNamespace(id=uuid4(), nombres="Ana", primer_apellido="Perez")
        note = SimpleNamespace(estudiante_id=student.id, estudiante=student, total=95, asignacion=assignment, asignacion_id=assignment.id, periodo=period)
        low_note = SimpleNamespace(total=60)

        assert self.service._percentage(1, 2) == 50
        assert self.service._percentage(0, 0) == 0
        assert self.service._is_positive_state("Presente") is True
        assert self.service._is_positive_state("Falta") is False
        assert self.service._attendance_rate([SimpleNamespace(estado="Presente"), SimpleNamespace(estado="Falta")]) == 50
        assert self.service._visible_courses_count([note, SimpleNamespace(asignacion_id="course-2")]) == 2
        assert self.service._current_period_name([note]) == "P1 2026"
        assert self.service._current_period_name([]) == "Sin periodo visible"
        assert self.service._subject_averages([note]) == [("Biologia", 95.0)]

        risk = self.service._build_risk_report([note, low_note])
        assert risk["cantidad"] == 1
        assert risk["porcentaje"] == 50

        top = self.service._build_top_students([note])
        assert top[0]["nombre"] == "Ana Perez"
        assert self.service._build_alerts([low_note], UsuarioFactory())[0]["tipo"] == "warning"

    @pytest.mark.django_db
    def test_build_courses_helper_with_database_data(self):
        usuario = UsuarioFactory()
        periodo = Periodos.objects.create(id=uuid4(), nombre="P1", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31", activo=True)
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=2, paralelo="B", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Biologia")
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
        estudiante = Estudiantes.objects.create(id=uuid4(), usuario=UsuarioFactory(), grado=grado, primer_apellido="Perez", nombres="Ana", ci="CI44")
        Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo, total=95)

        self.service.access_service.can_view_all_academic_data = lambda u: True
        self.service.access_service.get_assigned_assignment_ids = lambda u: [asign.id]

        courses = self.service._build_courses([SimpleNamespace(asignacion_id=asign.id, estudiante_id=estudiante.id, total=95)], usuario)
        assert courses[0]["nombre"] == "Biologia"

    @pytest.mark.django_db
    def test_build_report_document_generates_docx(self):
        usuario = UsuarioFactory()
        periodo = Periodos.objects.create(id=uuid4(), nombre="3er Trimestre", numero=3, gestion=2026, fecha_inicio="2026-09-01", fecha_fin="2026-11-30", activo=True)
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=2, paralelo="A", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="COMUNICACIÓN Y LENGUAJE")
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
        estudiante = Estudiantes.objects.create(
            id=uuid4(),
            usuario=UsuarioFactory(),
            grado=grado,
            primer_apellido="Perez",
            nombres="Ana",
            ci="CI100",
            genero="F",
        )
        Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo, total=65)

        document_bytes = self.service.build_report_document(usuario, periodo_id=periodo.id, trimestre=3)

        assert isinstance(document_bytes, bytes)
        assert document_bytes[:2] == b"PK"


# Agrega tests específicos para el servicio de reportes
