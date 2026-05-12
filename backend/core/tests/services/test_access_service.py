"""Tests para AccessControlService"""
import pytest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import patch

from core.services.access_service import AccessControlService
from core.tests.factories.user_factory import UsuarioFactory
from core.models import Roles, UsuarioRoles, Docentes, DocenteAsignacion, Grados


@pytest.mark.django_db
class TestAccessControlService:
    """Tests para el servicio de control de acceso"""

    def setup_method(self):
        """Configuración antes de cada test"""
        self.service = AccessControlService()

    def test_get_role_names_empty_for_none(self):
        assert self.service.get_role_names(None) == set()

    def test_get_role_names_and_normalization(self):
        user = UsuarioFactory()
        Roles.objects.create(id=uuid4(), nombre="DirecTór")
        role = Roles.objects.create(id=uuid4(), nombre="Profesor")
        # assign both roles to user
        UsuarioRoles.objects.create(id=uuid4(), usuario=user, rol=role, asignado_por=user, activo=True)

        # create direct role assignment with different case/accents on another user
        other_user = UsuarioFactory()
        direct_role = Roles.objects.create(id=uuid4(), nombre="Director")
        UsuarioRoles.objects.create(id=uuid4(), usuario=other_user, rol=direct_role, asignado_por=other_user, activo=True)

        # role names
        names = self.service.get_role_names(user)
        assert isinstance(names, set)

    def test_can_view_all_academic_data_true_for_director(self):
        director = UsuarioFactory()
        role = Roles.objects.create(id=uuid4(), nombre="Director")
        UsuarioRoles.objects.create(id=uuid4(), usuario=director, rol=role, asignado_por=director, activo=True)

        assert self.service.can_view_all_academic_data(director) is True

    def test_can_view_all_academic_data_false_without_roles(self):
        assert self.service.can_view_all_academic_data(None) is False

    def test_filter_students_queryset_scoped_by_grades(self):
        queryset = SimpleNamespace()

        class FakeQueryset:
            def none(self):
                return "none"

            def filter(self, **kwargs):
                return kwargs

        fake_queryset = FakeQueryset()
        with patch.object(self.service, "can_view_all_academic_data", return_value=False), \
                patch.object(self.service, "get_assigned_grade_ids", return_value=["grade-1", "grade-2"]):
            result = self.service.filter_students_queryset(fake_queryset, UsuarioFactory())

        assert result == {"grado_id__in": ["grade-1", "grade-2"]}

    def test_filter_students_queryset_returns_none_when_no_grades(self):
        class FakeQueryset:
            def none(self):
                return "none"

            def filter(self, **kwargs):
                return kwargs

        fake_queryset = FakeQueryset()
        with patch.object(self.service, "can_view_all_academic_data", return_value=False), \
                patch.object(self.service, "get_assigned_grade_ids", return_value=[]):
            result = self.service.filter_students_queryset(fake_queryset, UsuarioFactory())

        assert result == "none"

    def test_filter_courses_and_notes_for_admin(self):
        marker = object()
        with patch.object(self.service, "can_view_all_academic_data", return_value=True):
            assert self.service.filter_courses_queryset(marker, None) is marker
            assert self.service.filter_notes_queryset(marker, None) is marker

    def test_filter_courses_and_notes_for_teacher(self):
        class FakeQueryset:
            def filter(self, **kwargs):
                return kwargs

        fake_queryset = FakeQueryset()
        user = UsuarioFactory()
        with patch.object(self.service, "can_view_all_academic_data", return_value=False):
            courses = self.service.filter_courses_queryset(fake_queryset, user)
            notes = self.service.filter_notes_queryset(fake_queryset, user)

        assert courses == {"docente__usuario": user}
        assert notes == {"asignacion__docente__usuario": user}

    def test_build_permissions_payload(self):
        user = UsuarioFactory()
        with patch.object(self.service, "get_role_names", return_value={"secretaria", "director"}):
            payload = self.service.build_permissions_payload(user)

        assert payload == {
            "roles": ["director", "secretaria"],
            "puede_ver_todo": True,
            "puede_crear": True,
        }

    def test_normalize_role_strips_accents(self):
        assert self.service._normalize_role("Dirección") == "direccion"

    def test_get_assigned_grade_ids(self):
        usuario = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=usuario)
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        # create an area since area is NOT NULL
        from core.models import Areas
        area = Areas.objects.create(id=uuid4(), nombre="Matematica")
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)

        ids = self.service.get_assigned_grade_ids(usuario)
        assert isinstance(ids, list)
        assert str(grado.id) in [str(x) for x in ids] or grado.id in ids

