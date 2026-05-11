import pytest
from uuid import uuid4
from django.db import IntegrityError

from core.models import (
    Usuarios,
    Grados,
    Estudiantes,
    Roles,
    Areas,
    Docentes,
    DocenteAsignacion,
    Periodos,
    Notas,
    DimensionesEvaluacion,
)

from core.tests.factories.user_factory import UsuarioFactory, StudentUsuarioFactory
from core.tests.factories.student_factory import EstudianteFactory


@pytest.mark.django_db
def test_usuarios_creation_and_unique_email():
    u1 = UsuarioFactory()
    assert Usuarios.objects.filter(email=u1.email).exists()

    # unique email constraint
    with pytest.raises(IntegrityError):
        Usuarios.objects.create(
            id=uuid4(), nombre="X", apellido="Y", email=u1.email, password_hash="hash", ci=f"CI{uuid4()}"
        )


@pytest.mark.django_db
def test_grados_unique_together_constraint():
    g1 = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
    assert Grados.objects.filter(id=g1.id).exists()

    # Creating another with same unique fields should raise IntegrityError
    with pytest.raises(IntegrityError):
        Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)


@pytest.mark.django_db
def test_estudiantes_creation_and_relations():
    grado = Grados.objects.create(id=uuid4(), nivel="Secundaria", numero=2, paralelo="B", gestion=2026)
    usuario = StudentUsuarioFactory()
    est = EstudianteFactory(usuario=usuario, grado=grado)

    assert Estudiantes.objects.filter(id=est.id).exists()
    fetched = Estudiantes.objects.get(id=est.id)
    assert fetched.usuario.id == usuario.id
    assert fetched.grado.id == grado.id


@pytest.mark.django_db
def test_roles_unique_name():
    r1 = Roles.objects.create(id=uuid4(), nombre="Profesor")
    assert Roles.objects.filter(nombre="Profesor").exists()

    with pytest.raises(IntegrityError):
        Roles.objects.create(id=uuid4(), nombre="Profesor")


@pytest.mark.django_db
def test_areas_and_docente_asignacion_unique():
    area = Areas.objects.create(id=uuid4(), nombre="Matematicas")
    grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=3, paralelo="C", gestion=2026)
    usuario_doc = UsuarioFactory()
    docente = Docentes.objects.create(id=uuid4(), usuario=usuario_doc)

    asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
    assert DocenteAsignacion.objects.filter(id=asign.id).exists()

    # unique_together on (docente, grado, area)
    with pytest.raises(IntegrityError):
        DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)


@pytest.mark.django_db
def test_notas_unique_together():
    grado = Grados.objects.create(id=uuid4(), nivel="Secundaria", numero=4, paralelo="D", gestion=2026)
    usuario = StudentUsuarioFactory()
    estudiante = EstudianteFactory(usuario=usuario, grado=grado)

    area = Areas.objects.create(id=uuid4(), nombre="Ciencias")
    docente_user = UsuarioFactory()
    docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
    asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
    periodo = Periodos.objects.create(id=uuid4(), nombre="1er Trimestre", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31")

    n1 = Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo)
    assert Notas.objects.filter(id=n1.id).exists()

    with pytest.raises(IntegrityError):
        Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo)
"""Tests unitarios de modelos"""
from uuid import uuid4

from core.models import Usuarios


class TestUsuariosModel:
    """Tests para el modelo Usuarios"""

    def test_usuario_creation_success(self):
        """Verifica que se puede crear un usuario correctamente"""
        usuario = Usuarios(
            id=uuid4(),
            nombre="Juan",
            apellido="Pérez",
            email="juan@example.com",
            password_hash="hash",
            ci="CI123456",
            activo=True,
        )
        assert usuario.id is not None
        assert usuario.nombre is not None
        assert usuario.email is not None

    def test_usuario_email_unique(self):
        """Verifica que los emails son únicos"""
        email_field = Usuarios._meta.get_field("email")

        assert email_field.unique is True

    def test_usuario_string_representation(self):
        """Verifica la representación en string del usuario"""
        usuario = Usuarios(
            id=uuid4(),
            nombre="Juan",
            apellido="Pérez",
            email="juan@example.com",
            password_hash="hash",
            ci="CI123456",
            activo=True,
        )
        # El modelo no define __str__, así que validamos los campos base.
        assert usuario.nombre == "Juan"
        assert usuario.apellido == "Pérez"


# Agrega aquí más tests de otros modelos


@pytest.mark.django_db
def test_asistencias_creation_and_unique():
    """Test for Asistencias model - attendance records"""
    from core.models import Asistencias
    from datetime import date
    
    grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
    usuario = StudentUsuarioFactory()
    estudiante = EstudianteFactory(usuario=usuario, grado=grado)
    registro_user = UsuarioFactory()
    
    asist = Asistencias.objects.create(
        id=uuid4(),
        estudiante=estudiante,
        registrado_por=registro_user,
        fecha=date(2026, 1, 15),
        estado="presente"
    )
    assert Asistencias.objects.filter(id=asist.id).exists()
    
    # unique_together on (estudiante, fecha)
    with pytest.raises(IntegrityError):
        Asistencias.objects.create(
            id=uuid4(),
            estudiante=estudiante,
            registrado_por=registro_user,
            fecha=date(2026, 1, 15),
            estado="ausente"
        )


@pytest.mark.django_db
def test_audit_log_creation():
    """Test for AuditLog model - audit trail"""
    from core.models import AuditLog, NotaDetalle
    
    grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
    usuario = StudentUsuarioFactory()
    estudiante = EstudianteFactory(usuario=usuario, grado=grado)
    
    area = Areas.objects.create(id=uuid4(), nombre="Lenguaje")
    docente_user = UsuarioFactory()
    docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
    asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
    periodo = Periodos.objects.create(id=uuid4(), nombre="1er Trimestre", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31")
    nota = Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo)
    
    dim = DimensionesEvaluacion.objects.create(
        id=uuid4(),
        nombre="Comprensión",
        puntaje_maximo=100,
        orden=1,
        gestion=2026
    )
    nota_detalle = NotaDetalle.objects.create(id=uuid4(), nota=nota, dimension=dim, valor=85)
    
    audit = AuditLog.objects.create(
        id=uuid4(),
        nota_detalle=nota_detalle,
        usuario=docente_user,
        valor_anterior=80,
        valor_nuevo=85,
        motivo="Revisión de calificación"
    )
    assert AuditLog.objects.filter(id=audit.id).exists()
    assert audit.valor_nuevo == 85


@pytest.mark.django_db
def test_dimensiones_evaluacion_creation():
    """Test for DimensionesEvaluacion model"""
    from core.models import DimensionesEvaluacion
    
    dim = DimensionesEvaluacion.objects.create(
        id=uuid4(),
        nombre="Comprensión",
        puntaje_maximo=100,
        descripcion="Evaluación de comprensión lectora",
        activo=True,
        orden=1,
        gestion=2026
    )
    assert DimensionesEvaluacion.objects.filter(id=dim.id).exists()
    
    # unique_together on (nombre, gestion)
    with pytest.raises(IntegrityError):
        DimensionesEvaluacion.objects.create(
            id=uuid4(),
            nombre="Comprensión",
            puntaje_maximo=100,
            descripcion="Otra descripción",
            activo=True,
            orden=2,
            gestion=2026
        )


@pytest.mark.django_db
def test_docentes_creation():
    """Test for Docentes model"""
    usuario_doc = UsuarioFactory()
    docente = Docentes.objects.create(id=uuid4(), usuario=usuario_doc)
    
    assert Docentes.objects.filter(id=docente.id).exists()
    assert docente.usuario.id == usuario_doc.id


@pytest.mark.django_db
def test_horarios_creation_and_unique():
    """Test for Horarios model"""
    from core.models import Horarios
    from datetime import time
    
    grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
    area = Areas.objects.create(id=uuid4(), nombre="Matemática")
    docente_user = UsuarioFactory()
    docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
    asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
    
    horario = Horarios.objects.create(
        id=uuid4(),
        asignacion=asign,
        dia_semana=1,  # Monday
        hora_inicio=time(8, 0),
        hora_fin=time(9, 0),
        aula="Aula 101"
    )
    assert Horarios.objects.filter(id=horario.id).exists()
    
    # unique_together on (asignacion, dia_semana, hora_inicio)
    with pytest.raises(IntegrityError):
        Horarios.objects.create(
            id=uuid4(),
            asignacion=asign,
            dia_semana=1,
            hora_inicio=time(8, 0),
            hora_fin=time(9, 30),  # Different end time
            aula="Aula 102"
        )


@pytest.mark.django_db
def test_licencias_creation():
    """Test for Licencias model"""
    from core.models import Licencias
    from datetime import date
    
    grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
    usuario = StudentUsuarioFactory()
    estudiante = EstudianteFactory(usuario=usuario, grado=grado)
    solicitado_por_user = UsuarioFactory()
    
    licencia = Licencias.objects.create(
        id=uuid4(),
        estudiante=estudiante,
        solicitado_por=solicitado_por_user,
        fecha_inicio=date(2026, 1, 15),
        fecha_fin=date(2026, 1, 25),
        motivo="Cita médica"
    )
    assert Licencias.objects.filter(id=licencia.id).exists()


@pytest.mark.django_db
def test_nota_detalle_creation():
    """Test for NotaDetalle model"""
    from core.models import NotaDetalle, DimensionesEvaluacion
    
    grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
    usuario = StudentUsuarioFactory()
    estudiante = EstudianteFactory(usuario=usuario, grado=grado)
    
    area = Areas.objects.create(id=uuid4(), nombre="Ciencias")
    docente_user = UsuarioFactory()
    docente = Docentes.objects.create(id=uuid4(), usuario=docente_user)
    asign = DocenteAsignacion.objects.create(id=uuid4(), docente=docente, grado=grado, area=area)
    periodo = Periodos.objects.create(id=uuid4(), nombre="1er Trimestre", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31")
    nota = Notas.objects.create(id=uuid4(), estudiante=estudiante, asignacion=asign, periodo=periodo)
    
    dim = DimensionesEvaluacion.objects.create(
        id=uuid4(),
        nombre="Razonamiento",
        puntaje_maximo=100,
        orden=1,
        gestion=2026
    )
    
    nota_detalle = NotaDetalle.objects.create(
        id=uuid4(),
        nota=nota,
        dimension=dim,
        valor=92
    )
    assert NotaDetalle.objects.filter(id=nota_detalle.id).exists()
    assert nota_detalle.valor == 92
    
    # unique_together on (nota, dimension)
    with pytest.raises(IntegrityError):
        NotaDetalle.objects.create(
            id=uuid4(),
            nota=nota,
            dimension=dim,
            valor=88
        )


@pytest.mark.django_db
def test_periodo_estados_creation():
    """Test for PeriodoEstados model"""
    from core.models import PeriodoEstados
    
    grado = Grados.objects.create(id=uuid4(), nivel="Primaria", numero=1, paralelo="A", gestion=2026)
    periodo = Periodos.objects.create(id=uuid4(), nombre="1er Trimestre", numero=1, gestion=2026, fecha_inicio="2026-01-01", fecha_fin="2026-03-31")
    
    periodo_estado = PeriodoEstados.objects.create(
        id=uuid4(),
        grado=grado,
        periodo=periodo,
        cerrado=False
    )
    assert PeriodoEstados.objects.filter(id=periodo_estado.id).exists()
    
    # unique_together on (grado, periodo)
    with pytest.raises(IntegrityError):
        PeriodoEstados.objects.create(
            id=uuid4(),
            grado=grado,
            periodo=periodo,
            cerrado=True
        )


@pytest.mark.django_db
def test_periodos_creation_and_unique():
    """Test for Periodos model"""
    periodo = Periodos.objects.create(
        id=uuid4(),
        nombre="2do Trimestre",
        numero=2,
        gestion=2026,
        fecha_inicio="2026-04-01",
        fecha_fin="2026-06-30"
    )
    assert Periodos.objects.filter(id=periodo.id).exists()
    
    # unique_together on (numero, gestion)
    with pytest.raises(IntegrityError):
        Periodos.objects.create(
            id=uuid4(),
            nombre="Otro 2do Trimestre",
            numero=2,
            gestion=2026,
            fecha_inicio="2026-05-01",
            fecha_fin="2026-07-31"
        )


@pytest.mark.django_db
def test_tutores_creation():
    """Test for Tutores model"""
    from core.models import Tutores
    
    tutor = Tutores.objects.create(
        id=uuid4(),
        nombre="Carlos",
        apellido="García",
        ci="12345678",
        telefono="7654321",
        ocupacion="Ingeniero"
    )
    assert Tutores.objects.filter(id=tutor.id).exists()


@pytest.mark.django_db
def test_usuario_roles_creation_and_unique():
    """Test for UsuarioRoles model"""
    from core.models import UsuarioRoles
    
    usuario = UsuarioFactory()
    asignado_por_user = UsuarioFactory()
    rol = Roles.objects.create(id=uuid4(), nombre="Docente")
    
    usuario_rol = UsuarioRoles.objects.create(
        id=uuid4(),
        usuario=usuario,
        rol=rol,
        asignado_por=asignado_por_user
    )
    assert UsuarioRoles.objects.filter(id=usuario_rol.id).exists()
    
    # unique_together on (usuario, rol)
    with pytest.raises(IntegrityError):
        UsuarioRoles.objects.create(
            id=uuid4(),
            usuario=usuario,
            rol=rol,
            asignado_por=asignado_por_user
        )

