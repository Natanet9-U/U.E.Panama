"""Tests para SchedulesService"""
from datetime import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.services.schedules_service import SchedulesService


@pytest.mark.django_db
class TestSchedulesService:
    """Tests para el servicio de horarios"""

    def setup_method(self):
        self.service = SchedulesService()

    def test_get_school_hours(self):
        hours = self.service._get_school_hours()

        assert len(hours) == 8
        assert hours[0] == time(8, 0)
        assert hours[-1] == time(15, 0)

    def test_build_summary_empty(self):
        summary = self.service._build_summary([])

        assert summary[0]["valor"] == "0"
        assert summary[1]["valor"] == "0h"
        assert summary[2]["valor"] == "0"
        assert summary[3]["valor"] == "0h"

    def test_build_summary_with_data(self):
        schedules = [
            SimpleNamespace(hora_inicio=time(8, 0), hora_fin=time(9, 0), aula="A1"),
            SimpleNamespace(hora_inicio=time(9, 0), hora_fin=time(10, 30), aula="A2"),
        ]

        summary = self.service._build_summary(schedules)

        assert summary[0]["valor"] == "2"
        assert summary[1]["valor"] == "2.5h"
        assert summary[2]["valor"] == "2"

    def test_build_calendar_and_format_class(self):
        assignment = SimpleNamespace(
            area=SimpleNamespace(nombre="Matematica"),
            grado=SimpleNamespace(nivel="Primaria", numero=3, paralelo="A"),
            docente=SimpleNamespace(usuario=SimpleNamespace(nombre="Ana")),
        )
        schedule = SimpleNamespace(
            asignacion=assignment,
            dia_semana=0,
            hora_inicio=time(8, 0),
            hora_fin=time(9, 0),
            aula="A1",
        )

        with patch.object(self.service, "_count_students", return_value=18):
            calendar = self.service._build_calendar([schedule])

        assert calendar[0]["hora"] == "08:00"
        assert calendar[0]["clases"]["Lunes"][0]["asignatura"] == "Matematica"
        assert calendar[0]["clases"]["Lunes"][0]["estudiantes"] == 18

    def test_build_upcoming_classes(self):
        assignment = SimpleNamespace(
            area=SimpleNamespace(nombre="Ciencias"),
            grado=SimpleNamespace(nivel="Secundaria", numero=2, paralelo="B"),
            docente=SimpleNamespace(usuario=SimpleNamespace(nombre="Luis")),
        )
        schedule = SimpleNamespace(
            asignacion=assignment,
            dia_semana=2,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            aula="B1",
        )

        upcoming = self.service._build_upcoming_classes([schedule])

        assert len(upcoming) == 1
        assert upcoming[0]["asignatura"] == "Ciencias"
        assert upcoming[0]["grado"] == "Secundaria2B"
        assert upcoming[0]["docente"] == "Luis"

    def test_count_students_and_get_filtered_schedules_for_teacher(self):
        from uuid import uuid4
        from core.tests.factories.user_factory import UsuarioFactory
        from core.models import Areas, Grados, Docentes, DocenteAsignacion, Horarios, Estudiantes

        usuario = UsuarioFactory()
        area = Areas.objects.create(id=uuid4(), nombre="Musica")
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=3, paralelo="C", gestion=2026)
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
        Horarios.objects.create(id=uuid4(), asignacion=asign, dia_semana=0, hora_inicio=time(8, 0), hora_fin=time(9, 0), aula="A1")
        estudiante_user = UsuarioFactory()
        Estudiantes.objects.create(id=uuid4(), usuario=estudiante_user, grado=grado, primer_apellido="Perez", nombres="Ana", ci="CI10")

        with patch.object(self.service.access_control, "can_view_all_academic_data", return_value=False):
            schedules = self.service._get_filtered_schedules(docente_user)

        assert len(schedules) == 1
        assert self.service._count_students(asign) == 1

    def test_get_filtered_schedules_without_docente_returns_empty(self):
        from core.tests.factories.user_factory import UsuarioFactory

        user = UsuarioFactory()
        with patch.object(self.service.access_control, "can_view_all_academic_data", return_value=False):
            schedules = self.service._get_filtered_schedules(user)

        assert schedules == []

    def test_build_schedules_page_empty(self):
        with patch.object(self.service.access_control, "build_permissions_payload", return_value={"roles": [], "puede_ver_todo": False, "puede_crear": False}), \
                patch.object(self.service, "_get_filtered_schedules", return_value=[]):
            payload = self.service.build_schedules_page(None)

        assert payload["resumen"][0]["valor"] == "0"
        assert len(payload["calendario"]) == 8
        assert payload["calendario"][0]["hora"] == "08:00"
        assert payload["proximas_clases"] == []
