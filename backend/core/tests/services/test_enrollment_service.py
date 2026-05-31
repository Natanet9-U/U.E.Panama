"""Tests para EnrollmentService"""
from uuid import uuid4

import pytest

from core.models import Areas, DocenteAsignacion, Docentes, Estudiantes, Grados, Notas, Periodos, Tutores, Roles, UsuarioRoles
from core.services.enrollment_service import EnrollmentService
from core.tests.factories.user_factory import UsuarioFactory


@pytest.mark.django_db
class TestEnrollmentService:
    """Tests para el servicio de matriculas"""

    def setup_method(self):
        self.service = EnrollmentService()

    def test_search_existing_student_returns_payload(self):
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        estudiante = Estudiantes.objects.create(
            id=uuid4(),
            usuario=UsuarioFactory(),
            grado=grado,
            primer_apellido="Perez",
            nombres="Ana",
            ci="CI-100",
            rude="CI-100",
        )

        payload = self.service.search_existing_student("CI-100")

        assert payload["id"] == str(estudiante.id)
        assert payload["activo"] is True

    def test_search_existing_student_missing_returns_none(self):
        assert self.service.search_existing_student("CI-NO-EXISTE") is None

    def test_enroll_new_student_success_creates_notas(self):
        creator = UsuarioFactory()
        grado = Grados.objects.create(id=uuid4(), nivel="Secundaria", numero=2, paralelo="B", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Ciencias")
        docente = Docentes.objects.create(id=uuid4(), usuario=UsuarioFactory())
        DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
        Periodos.objects.create(
            id=uuid4(),
            nombre="P1",
            numero=1,
            gestion=2026,
            fecha_inicio="2026-01-01",
            fecha_fin="2026-03-31",
            activo=True,
        )
        Roles.objects.create(id=uuid4(), nombre="Estudiante")

        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(self.service.access_service, "can_create_academic_data", lambda u: True)
            payload = self.service.enroll_new_student(
                creator,
                {
                    "rude": "CI-200",
                    "nombres": "Laura",
                    "primer_apellido": "Mendez",
                    "ci": "CI-200",
                    "email": "laura@test.com",
                    "grado_id": grado.id,
                    "password": "Secret123",
                },
            )

        assert payload["ci"] == "CI-200"
        assert Estudiantes.objects.filter(ci="CI-200").exists()
        assert Notas.objects.filter(estudiante__ci="CI-200").count() == 1

    def test_re_enroll_existing_student_success(self):
        creator = UsuarioFactory()
        grado_actual = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        nuevo_grado = Grados.objects.create(id=uuid4(), nivel="Secundaria", numero=3, paralelo="C", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Arte")
        docente = Docentes.objects.create(id=uuid4(), usuario=UsuarioFactory())
        DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=nuevo_grado, area=area)
        Periodos.objects.create(
            id=uuid4(),
            nombre="P1",
            numero=1,
            gestion=2026,
            fecha_inicio="2026-01-01",
            fecha_fin="2026-03-31",
            activo=True,
        )
        usuario_estudiante = UsuarioFactory(activo=False)
        Estudiantes.objects.create(
            id=uuid4(),
            usuario=usuario_estudiante,
            grado=grado_actual,
            primer_apellido="Perez",
            nombres="Ana",
            ci="CI-300",
            rude="CI-300",
        )

        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(self.service.access_service, "can_create_academic_data", lambda u: True)
            payload = self.service.re_enroll_existing_student(creator, "CI-300", nuevo_grado.id)

        usuario_estudiante.refresh_from_db()
        assert usuario_estudiante.activo is True
        assert payload["grado_nuevo"] == "Secundaria 3C"

    def test_get_enrollment_catalogs_returns_grades_and_tutors(self):
        usuario = UsuarioFactory()
        Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        Tutores.objects.create(id=uuid4(), nombre="Carlos", apellido="Lopez")

        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(self.service.access_service, "can_create_academic_data", lambda u: True)
            payload = self.service.get_enrollment_catalogs(usuario)

        assert len(payload["grados"]) == 1
        assert len(payload["tutores"]) == 1