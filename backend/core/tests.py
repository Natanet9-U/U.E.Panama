from django.test import TestCase
from .models import Usuarios, Roles, Areas, Estudiantes, Grados, Tutores
from .auth_utils import build_token, decode_token
from django.utils import timezone
import uuid

class UsuariosModelTest(TestCase):
	def setUp(self):
		self.usuario = Usuarios.objects.create(
			id=uuid.uuid4(),
			nombre="Juan",
			apellido="Pérez",
			email="juan@example.com",
			password_hash="dummyhash",
			ci="12345678",
			telefono="88451156",
			activo=True,
			created_at=timezone.now()
		)

	def test_usuario_fields(self):
		self.assertEqual(self.usuario.nombre, "Juan")
		self.assertEqual(self.usuario.apellido, "Pérez")
		self.assertEqual(self.usuario.email, "juan@example.com")
		self.assertTrue(self.usuario.activo)
		self.assertEqual(self.usuario.ci, "12345678")

	def test_usuario_unicidad_email(self):
		with self.assertRaises(Exception):
			Usuarios.objects.create(
				id=uuid.uuid4(),
				nombre="Otro",
				apellido="Apellido",
				email="juan@example.com",
				password_hash="hash",
				ci="99999999",
				activo=True,
				created_at=timezone.now()
			)

class RolesModelTest(TestCase):
	def test_crear_rol(self):
		rol = Roles.objects.create(
			id=uuid.uuid4(),
			nombre="Administrador",
			descripcion="Rol de administrador con todos los permisos",
			activo=True,
			created_at=timezone.now()
		)
		self.assertEqual(rol.nombre, "Administrador")
		self.assertTrue(rol.activo)

class AreasModelTest(TestCase):
	def test_crear_area(self):
		area = Areas.objects.create(
			id=uuid.uuid4(),
			nombre="Matemáticas"
		)
		self.assertEqual(area.nombre, "Matemáticas")

class TutoresModelTest(TestCase):
	def test_crear_tutor(self):
		tutor = Tutores.objects.create(
			id=uuid.uuid4(),
			nombre="Pedro",
			apellido="Gómez",
			ci="TUT123",
			telefono="51887545",
			ocupacion="Abogado",
			direccion="Calle 123"
		)
		self.assertEqual(tutor.nombre, "Pedro")
		self.assertEqual(tutor.ocupacion, "Abogado")

class GradosModelTest(TestCase):
	def test_crear_grado(self):
		grado = Grados.objects.create(
			id=uuid.uuid4(),
			nivel="Primaria",
			numero=1,
			paralelo="A",
			gestion=2026,
			created_at=timezone.now()
		)
		self.assertEqual(grado.nivel, "Primaria")
		self.assertEqual(grado.numero, 1)

class EstudiantesModelTest(TestCase):
	def setUp(self):
		self.tutor = Tutores.objects.create(
			id=uuid.uuid4(), nombre="Tutor", apellido="Uno", ci="TUT1")
		self.grado = Grados.objects.create(
			id=uuid.uuid4(), nivel="Secundaria", numero=2, paralelo="B", gestion=2026)
		self.usuario = Usuarios.objects.create(
			id=uuid.uuid4(), nombre="Estu", apellido="Diant", email="estu@ex.com", password_hash="hash", ci="ESTU1")
		self.estudiante = Estudiantes.objects.create(
			id=uuid.uuid4(), usuario=self.usuario, grado=self.grado, primer_apellido="Diant", nombres="Estu", tutor=self.tutor)

	def test_estudiante_fields(self):
		self.assertEqual(self.estudiante.nombres, "Estu")
		self.assertEqual(self.estudiante.primer_apellido, "Diant")
		self.assertEqual(self.estudiante.tutor.nombre, "Tutor")

class AuthUtilsTest(TestCase):
	def test_crear_decodigocar_token(self):
		user_id = "test-user-id"
		token = build_token(user_id)
		decoded_id, error = decode_token(token)
		self.assertEqual(decoded_id, user_id)
		self.assertIsNone(error)