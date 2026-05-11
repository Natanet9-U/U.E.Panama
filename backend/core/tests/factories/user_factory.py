"""Factories para crear datos de prueba de Usuarios"""
import factory
from django.contrib.auth.hashers import make_password
from uuid import uuid4

from core.models import Usuarios


class UsuarioFactory(factory.django.DjangoModelFactory):
    """Factory para crear usuarios de prueba"""

    class Meta:
        model = Usuarios

    id = factory.LazyFunction(uuid4)
    nombre = factory.Faker("first_name", locale="es_ES")
    apellido = factory.Faker("last_name", locale="es_ES")
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password_hash = factory.LazyFunction(lambda: make_password("TestPassword123!"))
    ci = factory.Sequence(lambda n: f"CI{1000000 + n}")
    activo = True

    @classmethod
    def create(cls, **kwargs):
        """Override para asegurar que la contraseña está hasheada"""
        if "password_hash" in kwargs and not kwargs["password_hash"].startswith("pbkdf2"):
            kwargs["password_hash"] = make_password(kwargs["password_hash"])
        return super().create(**kwargs)


class AdminUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios administradores"""
    nombre = "Admin"
    apellido = "Usuario"
    email = factory.Sequence(lambda n: f"admin{n}@test.com")


class TeacherUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios docentes"""
    nombre = "Docente"
    apellido = "Usuario"
    email = factory.Sequence(lambda n: f"teacher{n}@test.com")


class StudentUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios estudiantes"""
    nombre = "Estudiante"
    apellido = "Usuario"
    email = factory.Sequence(lambda n: f"student{n}@test.com")
