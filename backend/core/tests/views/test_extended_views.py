"""Tests para las vistas nuevas del backend"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.models import Areas, ActividadNotas, Actividades, Asistencias, DocenteAsignacion, Docentes, Estudiantes, Grados, Notas, Periodos, Usuarios, DimensionesEvaluacion
from core.views import (
    actividades_notas_estudiante_view,
    actividades_notas_view,
    actividades_view,
    attendance_view,
    change_password_view,
    course_detail_view,
    docentes_view,
    enrollment_catalogs_view,
    enrollment_new_view,
    enrollment_re_enroll_view,
    enrollment_search_view,
    grades_update_view,
    licencias_view,
    recompute_actividades_view,
)


@pytest.mark.django_db
class TestExtendedViews:
    def setup_method(self):
        self.factory = APIRequestFactory()

    def _auth_user(self):
        return SimpleNamespace(id="user-1", activo=True, nombre="Ana", apellido="Perez", email="ana@test.com")

    def test_login_view_warms_dashboard_cache(self):
        from core.views import login_view

        request = self.factory.post("/api/login/", {"email": "test@test.com", "password": "Secret123"}, format="json")
        usuario = Usuarios.objects.create(
            id=uuid4(),
            nombre="Ana",
            apellido="Perez",
            email="test@test.com",
            password_hash=make_password("Secret123"),
            ci="CI-900",
            activo=True,
        )

        with patch("core.views.Usuarios.objects.get", return_value=usuario), \
                patch("core.views.check_password", return_value=True), \
                patch("core.views.build_token", return_value="signed-token"), \
                patch("core.views.DashboardService.warm_cache_for_user") as warm_cache:
            response = login_view(request)

        warm_cache.assert_called_once_with(usuario)
        assert response.status_code == status.HTTP_200_OK

    def test_attendance_view_post_delegates(self):
        request = self.factory.post("/api/attendance/", {"asignacion_id": "asg-1", "fecha": "2026-05-21", "estados": {}}, format="json")
        request.usuario = self._auth_user()

        with patch("core.views.AttendanceService.mark_attendance", return_value=["att-1"]) as mark_attendance:
            response = attendance_view(request)

        mark_attendance.assert_called_once()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["ids"] == ["att-1"]

    @pytest.mark.django_db
    def test_attendance_view_get_returns_records(self):
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Matematica")
        docente = Docentes.objects.create(id=uuid4(), usuario=Usuarios.objects.create(id=uuid4(), nombre="Doc", apellido="Ent", email="doc@test.com", password_hash="x", ci="CI-DOC", activo=True))
        asignacion = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
        estudiante = Estudiantes.objects.create(id=uuid4(), usuario=Usuarios.objects.create(id=uuid4(), nombre="Est", apellido="Uno", email="est@test.com", password_hash="x", ci="CI-EST", activo=True), grado=grado, primer_apellido="Uno", nombres="Est", ci="CI-EST")
        Asistencias.objects.create(id=uuid4(), estudiante=estudiante, registrado_por=docente.usuario, fecha=date(2026, 5, 21), estado="Presente")

        request = self.factory.get("/api/attendance/?asignacion_id=%s&fecha=2026-05-21" % asignacion.id)
        request.usuario = self._auth_user()

        response = attendance_view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["asistencias"][0]["estado"] == "Presente"

    def test_licencias_view_success(self):
        request = self.factory.post("/api/licencias/", {"estudiante_id": "student-1"}, format="json")
        request.usuario = self._auth_user()

        with patch("core.views.AttendanceService.create_licencia", return_value={"id": "lic-1"}) as create_licencia:
            response = licencias_view(request)

        create_licencia.assert_called_once()
        assert response.status_code == status.HTTP_201_CREATED

    def test_docentes_view_get_delegates(self):
        request = self.factory.get("/api/docentes/?query=Ana&page=2&page_size=4")
        request.usuario = self._auth_user()

        payload = {"docentes": [], "paginacion": {}, "permisos": {}}
        with patch("core.views.DocentesService.build_docentes_page", return_value=payload) as build_docentes_page:
            response = docentes_view(request)

        build_docentes_page.assert_called_once_with(request.usuario, query="Ana", page="2", page_size="4")
        assert response.status_code == status.HTTP_200_OK

    def test_docentes_view_post_delegates(self):
        request = self.factory.post("/api/docentes/", {"nombres": "Laura", "apellido": "Mendez"}, format="json")
        request.usuario = self._auth_user()

        with patch("core.views.DocentesService.create_docente", return_value={"id": "doc-1"}) as create_docente:
            response = docentes_view(request)

        create_docente.assert_called_once()
        assert response.status_code == status.HTTP_201_CREATED

    def test_enrollment_search_view_found(self):
        request = self.factory.get("/api/enrollment/search/?rude=CI-1")
        request.usuario = self._auth_user()

        with patch("core.views.EnrollmentService.search_existing_student", return_value={"id": "student-1"}) as search_existing_student:
            response = enrollment_search_view(request)

        search_existing_student.assert_called_once_with("CI-1")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["encontrado"] is True

    def test_enrollment_new_view_delegates(self):
        request = self.factory.post("/api/enrollment/new/", {"ci": "CI-2"}, format="json")
        request.usuario = self._auth_user()

        with patch("core.views.EnrollmentService.enroll_new_student", return_value={"id": "student-1"}) as enroll_new_student:
            response = enrollment_new_view(request)

        enroll_new_student.assert_called_once()
        assert response.status_code == status.HTTP_201_CREATED

    def test_enrollment_re_enroll_view_validates_required_fields(self):
        request = self.factory.post("/api/enrollment/re-enroll/", {"ci": ""}, format="json")
        request.usuario = self._auth_user()

        response = enrollment_re_enroll_view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_enrollment_catalogs_view_delegates(self):
        request = self.factory.get("/api/enrollment/catalogs/")
        request.usuario = self._auth_user()

        with patch("core.views.EnrollmentService.get_enrollment_catalogs", return_value={"grados": [], "tutores": []}) as get_catalogs:
            response = enrollment_catalogs_view(request)

        get_catalogs.assert_called_once_with(request.usuario)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_course_detail_view_returns_payload(self):
        periodo = Periodos.objects.create(id=uuid4(), nombre="P1", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31", activo=True)
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Arte")
        docente = Docentes.objects.create(id=uuid4(), usuario=Usuarios.objects.create(id=uuid4(), nombre="Doc", apellido="Ent", email="doc2@test.com", password_hash="x", ci="CI-DOC2", activo=True))
        asignacion = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
        estudiante = Estudiantes.objects.create(id=uuid4(), usuario=Usuarios.objects.create(id=uuid4(), nombre="Est", apellido="Dos", email="est2@test.com", password_hash="x", ci="CI-EST2", activo=True), grado=grado, primer_apellido="Dos", nombres="Est", ci="CI-EST2")
        dimension = DimensionesEvaluacion.objects.create(id=uuid4(), nombre="Participacion", puntaje_maximo=100, orden=1, gestion=2026)
        nota = Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asignacion, periodo=periodo, total=90)
        from core.models import NotaDetalle
        NotaDetalle.objects.create(id=uuid4(), nota=nota, dimension=dimension, valor=90)

        request = self.factory.get(f"/api/course-detail/?asignacion_id={asignacion.id}&periodo_id={periodo.id}")
        request.usuario = self._auth_user()

        response = course_detail_view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["estudiantes"][0]["id"] == str(estudiante.id)
        assert response.data["notas"][0]["total"] == 90

    def test_grades_update_view_delegates(self):
        request = self.factory.post("/api/grades/update/", {"asignacion_id": "asg-1", "periodo_id": "per-1", "notas": []}, format="json")
        request.usuario = self._auth_user()

        with patch("core.views.GradesService.update_student_grades", return_value=["note-1"]) as update_student_grades:
            response = grades_update_view(request)

        update_student_grades.assert_called_once()
        assert response.status_code == status.HTTP_200_OK

    def test_recompute_actividades_view_delegates(self):
        request = self.factory.post("/api/grades/recompute/", {"asignacion_id": "asg-1", "periodo_id": "per-1"}, format="json")
        request.usuario = self._auth_user()

        with patch("core.views.GradesService.recompute_from_actividades", return_value=3) as recompute_from_actividades:
            response = recompute_actividades_view(request)

        recompute_from_actividades.assert_called_once()
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_activities_view_get_and_post(self):
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Musica")
        docente = Docentes.objects.create(id=uuid4(), usuario=Usuarios.objects.create(id=uuid4(), nombre="Doc", apellido="Act", email="doc3@test.com", password_hash="x", ci="CI-DOC3", activo=True))
        asignacion = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)

        get_request = self.factory.get(f"/api/activities/?asignacion_id={asignacion.id}")
        get_request.usuario = self._auth_user()
        get_response = actividades_view(get_request)
        assert get_response.status_code == status.HTTP_200_OK

        # create a valid dimension and include its id in the post payload
        dimension = DimensionesEvaluacion.objects.create(id=uuid4(), nombre="Evaluacion", puntaje_maximo=100, orden=1, gestion=2026, activo=True)
        post_request = self.factory.post("/api/activities/", {"asignacion_id": str(asignacion.id), "nombre": "Examen", "dimension_id": str(dimension.id)}, format="json")
        post_request.usuario = self._auth_user()
        with patch("core.views.AccessControlService.can_view_all_academic_data", return_value=True), \
                patch("core.views.AccessControlService.get_assigned_assignment_ids", return_value=[]):
            post_response = actividades_view(post_request)

        assert post_response.status_code == status.HTTP_201_CREATED
        assert Actividades.objects.filter(asignacion=asignacion, nombre="Examen").exists()

    @pytest.mark.django_db
    def test_activities_notas_view_and_estudiante_view(self):
        grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
        area = Areas.objects.create(id=uuid4(), nombre="Musica")
        docente = Docentes.objects.create(id=uuid4(), usuario=Usuarios.objects.create(id=uuid4(), nombre="Doc", apellido="Act", email="doc4@test.com", password_hash="x", ci="CI-DOC4", activo=True))
        asignacion = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
        estudiante = Estudiantes.objects.create(id=uuid4(), usuario=Usuarios.objects.create(id=uuid4(), nombre="Est", apellido="Act", email="est4@test.com", password_hash="x", ci="CI-EST4", activo=True), grado=grado, primer_apellido="Act", nombres="Est", ci="CI-EST4")
        actividad = Actividades.objects.create(id=uuid4(), asignacion=asignacion, nombre="Tarea 1", puntaje_maximo=100)

        request = self.factory.post("/api/activities/notas/", {"actividad_id": str(actividad.id), "notas": {str(estudiante.id): 88}}, format="json")
        request.usuario = self._auth_user()
        with patch("core.views.AccessControlService.can_view_all_academic_data", return_value=True), \
                patch("core.views.AccessControlService.get_assigned_assignment_ids", return_value=[]):
            response = actividades_notas_view(request)

        assert response.status_code == status.HTTP_200_OK
        assert ActividadNotas.objects.filter(actividad=actividad, estudiante=estudiante, valor=88).exists()

        get_request = self.factory.get(f"/api/activities/notas-estudiante/?asignacion_id={asignacion.id}&estudiante_id={estudiante.id}")
        get_request.usuario = self._auth_user()
        get_response = actividades_notas_estudiante_view(get_request)

        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data["notas"][str(actividad.id)] == 88

    def test_change_password_view_success(self):
        usuario = Usuarios.objects.create(id=uuid4(), nombre="Ana", apellido="Perez", email="pass@test.com", password_hash=make_password("OldPass123"), ci="CI-PASS", activo=True)
        request = self.factory.post("/api/password/", {"current_password": "OldPass123", "new_password": "NewPass123"}, format="json")
        request.usuario = usuario

        response = change_password_view(request)
        usuario.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert check_password("NewPass123", usuario.password_hash)