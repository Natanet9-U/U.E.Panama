"""Tests para DashboardService"""
import pytest
from core.services.dashboard_service import DashboardService


@pytest.mark.django_db
class TestDashboardService:
    """Tests para el servicio de dashboard"""

    def setup_method(self):
        """Configuración antes de cada test"""
        self.service = DashboardService()

    def test_placeholder(self):
        """Placeholder para tests de dashboard"""
        pass

    def test_build_dashboard_structure(self):
        from uuid import uuid4
        from core.tests.factories.user_factory import UsuarioFactory
        from core.models import Periodos, Grados, Usuarios, Estudiantes, Roles, Docentes, DocenteAsignacion, Areas, Notas, Asistencias
        from django.utils import timezone

        usuario = UsuarioFactory()
        periodo = Periodos.objects.create(id=uuid4(), nombre="P1", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31", activo=True)
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Arte")
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)

        # student and nota
        est_user = UsuarioFactory()
        estudiante = Estudiantes.objects.create(id=uuid4(), usuario=est_user, grado=grado, primer_apellido="X", nombres="Y", ci="CI2")
        Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo, total=85, created_at=timezone.now())

        # asistencia today
        Asistencias.objects.create(id=uuid4(), estudiante=estudiante, registrado_por=usuario, fecha=timezone.localdate(), estado="Presente")

        service = DashboardService()
        dash = service.build_dashboard(None)

        assert "resumen" in dash
        assert "asistencia_semanal" in dash
        assert isinstance(dash["resumen"], list)


# Agrega tests específicos para el servicio de dashboard
