"""Factories para crear datos de prueba de Estudiantes"""
import factory
from uuid import uuid4

from core.models import Estudiantes, Grados
from .user_factory import StudentUsuarioFactory


class EstudianteFactory(factory.django.DjangoModelFactory):
    """Factory para crear estudiantes de prueba"""

    class Meta:
        model = Estudiantes

    id = factory.LazyFunction(uuid4)
    nombres = factory.Faker("first_name", locale="es_ES")
    primer_apellido = factory.Faker("last_name", locale="es_ES")
    segundo_apellido = factory.Faker("last_name", locale="es_ES")
    ci = factory.Sequence(lambda n: f"{1000000 + n}")
    usuario = factory.SubFactory(StudentUsuarioFactory)
    grado = factory.LazyAttribute(lambda o: Grados.objects.first())  # Usa el primer grado disponible
    estado = "activo"
