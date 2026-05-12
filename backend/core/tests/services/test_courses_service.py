"""Tests para CoursesService"""
import pytest
from core.services.courses_service import CoursesService


@pytest.mark.django_db
class TestCoursesService:
    """Tests para el servicio de cursos"""

    def setup_method(self):
        """Configuración antes de cada test"""
        self.service = CoursesService()

    def test_placeholder(self):
        """Placeholder para tests de cursos"""
        pass

    def test_build_courses_page_returns_courses(self):
        from uuid import uuid4
        from core.tests.factories.user_factory import UsuarioFactory
        from core.models import Areas, Grados, Docentes, DocenteAsignacion, Estudiantes, Notas, Periodos

        usuario = UsuarioFactory()
        area = Areas.objects.create(id=uuid4(), nombre="Matematicas")
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
        asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)

        # create a student to count
        est_user = UsuarioFactory()
        Estudiantes.objects.create(id=uuid4(), usuario=est_user, grado=grado, primer_apellido="X", nombres="Y", ci="CI1")

        service = CoursesService()
        res = service.build_courses_page(usuario)

        assert "cursos" in res
        assert isinstance(res["cursos"], list)

    def test_create_course_permission_denied(self):
        service = CoursesService()
        usuario = None
        with pytest.raises(PermissionError):
            service.create_course(usuario, {})

    def test_create_course_success(self):
        from uuid import uuid4
        from core.tests.factories.user_factory import UsuarioFactory
        from core.models import Areas, Grados, Docentes, DocenteAsignacion

        creator = UsuarioFactory()
        area = Areas.objects.create(id=uuid4(), nombre="Ciencias")
        grado = Grados.objects.create(id=uuid4(), nivel="Secundaria", numero=2, paralelo="B", gestion=2026)
        docente_user = UsuarioFactory()
        docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)

        service = CoursesService()
        # allow creation
        service.access_service.can_create_academic_data = lambda u: True

        data = {"area_id": area.id, "grado_id": grado.id, "docente_id": docente.id}
        res = service.create_course(creator, data)
        assert "id" in res


# Agrega tests específicos para el servicio de cursos
