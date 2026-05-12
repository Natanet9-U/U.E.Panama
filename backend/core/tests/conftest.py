from types import SimpleNamespace
from uuid import uuid4

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Cliente API REST para pruebas"""
    return APIClient()


@pytest.fixture
def admin_user():
    """Crea un usuario administrador para pruebas"""
    return SimpleNamespace(
        id=uuid4(),
        nombre="Admin",
        apellido="Test",
        email="admin@test.com",
        password_hash="pbkdf2_sha256$dummy",
        ci="CI00000001",
        telefono="",
        activo=True,
    )


@pytest.fixture
def teacher_user():
    """Crea un usuario docente para pruebas"""
    return SimpleNamespace(
        id=uuid4(),
        nombre="Docente",
        apellido="Test",
        email="teacher@test.com",
        password_hash="pbkdf2_sha256$dummy",
        ci="CI00000002",
        telefono="",
        activo=True,
    )


@pytest.fixture
def student_user():
    """Crea un usuario estudiante para pruebas"""
    return SimpleNamespace(
        id=uuid4(),
        nombre="Estudiante",
        apellido="Test",
        email="student@test.com",
        password_hash="pbkdf2_sha256$dummy",
        ci="CI00000003",
        telefono="",
        activo=True,
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Cliente API autenticado como admin"""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def teacher_client(api_client, teacher_user):
    """Cliente API autenticado como docente"""
    api_client.force_authenticate(user=teacher_user)
    return api_client


@pytest.fixture
def student_client(api_client, student_user):
    """Cliente API autenticado como estudiante"""
    api_client.force_authenticate(user=student_user)
    return api_client
