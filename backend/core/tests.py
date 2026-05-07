from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase
from rest_framework.test import APIRequestFactory

from .views import courses_view, dashboard_view, grades_view, reports_view, schedules_view, students_view


class DashboardViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	@patch("core.views.DashboardService.build_dashboard")
	def test_dashboard_returns_payload_from_service(self, build_dashboard):
		build_dashboard.return_value = {
			"resumen": [],
			"asistencia_semanal": {"labels": [], "data": []},
			"promedio_por_asignatura": {"labels": [], "data": []},
			"rendimiento": [],
			"proximas_clases": [],
			"actividad_reciente": [],
			"tareas_pendientes": {"cantidad": 0, "mensaje": "", "detalle": ""},
			"estudiantes_destacados": [],
			"periodo_activo": None,
		}

		request = self.factory.get("/api/dashboard/")
		request.usuario = MagicMock()

		response = dashboard_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["resumen"], [])
		build_dashboard.assert_called_once()

	def test_dashboard_requires_authenticated_user(self):
		request = self.factory.get("/api/dashboard/")

		response = dashboard_view(request)

		self.assertEqual(response.status_code, 401)


class StudentsViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.api_factory = APIRequestFactory()

	@patch("core.views.StudentsService.build_students_page")
	def test_students_returns_payload_from_service(self, build_students_page):
		build_students_page.return_value = {
			"resumen": [],
			"estudiantes": [],
			"paginacion": {"pagina": 1, "tamano": 8, "total": 0, "paginas": 1, "siguiente": False, "anterior": False},
			"filtros": {"grados": [], "periodo_activo": None},
		}

		request = self.factory.get("/api/students/?query=ana&page=1")
		request.usuario = MagicMock()
		request.query_params = request.GET

		response = students_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["estudiantes"], [])
		build_students_page.assert_called_once()

	def test_students_requires_authenticated_user(self):
		request = self.factory.get("/api/students/")
		request.query_params = request.GET

		response = students_view(request)

		self.assertEqual(response.status_code, 401)

	@patch("core.views.StudentsService.create_student")
	def test_students_create_returns_created_payload(self, create_student):
		create_student.return_value = {"id": "1", "nombre": "Ana Perez"}
		request = self.api_factory.post("/api/students/", {"nombres": "Ana", "primer_apellido": "Perez", "email": "ana@example.com", "ci": "123", "grado_id": "g1"}, format="json")
		request.usuario = MagicMock()

		response = students_view(request)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["estudiante"]["nombre"], "Ana Perez")
		create_student.assert_called_once()


class CoursesViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.api_factory = APIRequestFactory()

	@patch("core.views.CoursesService.build_courses_page")
	def test_courses_returns_payload_from_service(self, build_courses_page):
		build_courses_page.return_value = {
			"resumen": [],
			"cursos": [],
			"paginacion": {"pagina": 1, "tamano": 6, "total": 0, "paginas": 1, "siguiente": False, "anterior": False},
			"permisos": {"roles": [], "puede_ver_todo": False, "puede_crear": False},
		}

		request = self.factory.get("/api/courses/?query=mat")
		request.usuario = MagicMock()
		request.query_params = request.GET

		response = courses_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["cursos"], [])
		build_courses_page.assert_called_once()

	def test_courses_requires_authenticated_user(self):
		request = self.factory.get("/api/courses/")
		request.query_params = request.GET

		response = courses_view(request)

		self.assertEqual(response.status_code, 401)

	@patch("core.views.CoursesService.create_course")
	def test_courses_create_returns_created_payload(self, create_course):
		create_course.return_value = {"id": "1", "nombre": "Matematicas"}
		request = self.api_factory.post("/api/courses/", {"area_id": "a1", "grado_id": "g1", "docente_id": "d1"}, format="json")
		request.usuario = MagicMock()

		response = courses_view(request)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["curso"]["nombre"], "Matematicas")
		create_course.assert_called_once()


class GradesViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	@patch("core.views.GradesService.build_grades_page")
	def test_grades_returns_payload_from_service(self, build_grades_page):
		build_grades_page.return_value = {
			"resumen": [],
			"calificaciones": [],
			"paginacion": {"pagina": 1, "tamano": 10, "total": 0, "paginas": 1, "siguiente": False, "anterior": False},
			"filtros": {"periodos": []},
			"permisos": {"roles": [], "puede_ver_todo": False, "puede_crear": False},
		}

		request = self.factory.get("/api/grades/?query=ana")
		request.usuario = MagicMock()
		request.query_params = request.GET

		response = grades_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["calificaciones"], [])
		build_grades_page.assert_called_once()


class ReportsViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	@patch("core.views.ReportsService.build_reports_page")
	def test_reports_returns_payload_from_service(self, build_reports_page):
		build_reports_page.return_value = {
			"resumen": [],
			"reportes": [],
			"top_estudiantes": [],
			"alertas": [],
			"cursos": [],
			"filtros": {"periodos": []},
			"permisos": {"roles": [], "puede_ver_todo": False, "puede_crear": False},
		}

		request = self.factory.get("/api/reports/")
		request.usuario = MagicMock()

		response = reports_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["reportes"], [])
		build_reports_page.assert_called_once()


class SchedulesViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()

	@patch("core.views.SchedulesService.build_schedules_page")
	def test_schedules_returns_payload_from_service(self, build_schedules_page):
		build_schedules_page.return_value = {
			"resumen": [],
			"calendario": [],
			"proximas_clases": [],
			"permisos": {"roles": [], "puede_ver_todo": False, "puede_crear": False},
		}

		request = self.factory.get("/api/schedules/")
		request.usuario = MagicMock()
		request.query_params = request.GET

		response = schedules_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["calendario"], [])
		build_schedules_page.assert_called_once()

	def test_schedules_requires_authenticated_user(self):
		request = self.factory.get("/api/schedules/")
		request.query_params = request.GET

		response = schedules_view(request)

		self.assertEqual(response.status_code, 401)
