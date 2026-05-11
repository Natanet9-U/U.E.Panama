from django.db import models

class Areas(models.Model):
	id = models.UUIDField(primary_key=True)
	nombre = models.TextField(unique=True)

	class Meta:
		managed = True
		db_table = 'areas'

class Asistencias(models.Model):
	id = models.UUIDField(primary_key=True)
	estudiante = models.ForeignKey('Estudiantes', models.DO_NOTHING)
	registrado_por = models.ForeignKey('Usuarios', models.DO_NOTHING, db_column='registrado_por')
	fecha = models.DateField()
	estado = models.TextField()
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'asistencias'
		unique_together = (('estudiante', 'fecha'),)

class AuditLog(models.Model):
	id = models.UUIDField(primary_key=True)
	nota_detalle = models.ForeignKey('NotaDetalle', models.DO_NOTHING)
	usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
	valor_anterior = models.IntegerField(blank=True, null=True)
	valor_nuevo = models.IntegerField(blank=True, null=True)
	motivo = models.TextField(blank=True, null=True)
	fecha_cambio = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'audit_log'

class DimensionesEvaluacion(models.Model):
	id = models.UUIDField(primary_key=True)
	nombre = models.TextField()
	puntaje_maximo = models.IntegerField()
	descripcion = models.TextField(blank=True, null=True)
	activo = models.BooleanField(blank=True, null=True)
	orden = models.IntegerField()
	gestion = models.IntegerField()

	class Meta:
		managed = True
		db_table = 'dimensiones_evaluacion'
		unique_together = (('nombre', 'gestion'),)

# Django framework models (admin, sessions, contenttypes) are managed by Django itself
# They should not be redefined here

class DocenteAsignacion(models.Model):
	id = models.UUIDField(primary_key=True)
	docente = models.ForeignKey('Docentes', models.DO_NOTHING)
	grado = models.ForeignKey('Grados', models.DO_NOTHING)
	area = models.ForeignKey(Areas, models.DO_NOTHING)

	class Meta:
		managed = True
		db_table = 'docente_asignacion'
		unique_together = (('docente', 'grado', 'area'),)

class Docentes(models.Model):
	id = models.UUIDField(primary_key=True)
	usuario = models.OneToOneField('Usuarios', models.DO_NOTHING)
	titulo_academico = models.TextField(blank=True, null=True)
	especialidad = models.TextField(blank=True, null=True)
	fecha_ingreso_institucion = models.DateField(blank=True, null=True)
	anos_experiencia = models.IntegerField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'docentes'

class Estudiantes(models.Model):
	id = models.UUIDField(primary_key=True)
	usuario = models.OneToOneField('Usuarios', models.DO_NOTHING)
	grado = models.ForeignKey('Grados', models.DO_NOTHING)
	primer_apellido = models.TextField(unique=True)
	segundo_apellido = models.TextField(blank=True, null=True)
	nombres = models.TextField()
	ci = models.TextField(unique=True, blank=True, null=True)
	fecha_nacimiento = models.DateField(blank=True, null=True)
	genero = models.CharField(max_length=1, blank=True, null=True)
	estado = models.TextField(blank=True, null=True)
	tutor = models.ForeignKey('Tutores', models.DO_NOTHING, blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'estudiantes'

class Grados(models.Model):
	id = models.UUIDField(primary_key=True)
	nivel = models.TextField()
	numero = models.IntegerField()
	paralelo = models.CharField(max_length=1)
	gestion = models.IntegerField()
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'grados'
		unique_together = (('nivel', 'numero', 'paralelo', 'gestion'),)

class Licencias(models.Model):
	id = models.UUIDField(primary_key=True)
	estudiante = models.ForeignKey(Estudiantes, models.DO_NOTHING)
	solicitado_por = models.ForeignKey('Usuarios', models.DO_NOTHING, db_column='solicitado_por')
	fecha_inicio = models.DateField()
	fecha_fin = models.DateField()
	motivo = models.TextField(blank=True, null=True)
	requiere_certificado = models.BooleanField(blank=True, null=True)
	certificado_adjunto = models.TextField(blank=True, null=True)
	aprobado = models.BooleanField(blank=True, null=True)
	aprobado_por = models.ForeignKey('Usuarios', models.DO_NOTHING, db_column='aprobado_por', related_name='licencias_aprobado_por_set', blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'licencias'

class NotaDetalle(models.Model):
	id = models.UUIDField(primary_key=True)
	nota = models.ForeignKey('Notas', models.DO_NOTHING)
	dimension = models.ForeignKey(DimensionesEvaluacion, models.DO_NOTHING)
	valor = models.IntegerField()
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'nota_detalle'
		unique_together = (('nota', 'dimension'),)

class Notas(models.Model):
	id = models.UUIDField(primary_key=True)
	estudiante = models.ForeignKey(Estudiantes, models.DO_NOTHING)
	asignacion = models.ForeignKey(DocenteAsignacion, models.DO_NOTHING)
	periodo = models.ForeignKey('Periodos', models.DO_NOTHING)
	total = models.IntegerField(blank=True, null=True)
	indicador = models.TextField(blank=True, null=True)
	observaciones = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)
	updated_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'notas'
		unique_together = (('estudiante', 'asignacion', 'periodo'),)

class PeriodoEstados(models.Model):
	id = models.UUIDField(primary_key=True)
	grado = models.ForeignKey(Grados, models.DO_NOTHING)
	periodo = models.ForeignKey('Periodos', models.DO_NOTHING)
	cerrado = models.BooleanField(blank=True, null=True)
	cerrado_por = models.ForeignKey('Usuarios', models.DO_NOTHING, db_column='cerrado_por', blank=True, null=True)
	fecha_cierre = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'periodo_estados'
		unique_together = (('grado', 'periodo'),)

class Periodos(models.Model):
	id = models.UUIDField(primary_key=True)
	nombre = models.TextField()
	numero = models.IntegerField()
	gestion = models.IntegerField()
	fecha_inicio = models.DateField()
	fecha_fin = models.DateField()
	activo = models.BooleanField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'periodos'
		unique_together = (('numero', 'gestion'),)

class Roles(models.Model):
	id = models.UUIDField(primary_key=True)
	nombre = models.TextField(unique=True)
	descripcion = models.TextField(blank=True, null=True)
	activo = models.BooleanField(blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'roles'

class Tutores(models.Model):
	id = models.UUIDField(primary_key=True)
	nombre = models.TextField()
	apellido = models.TextField(blank=True, null=True)
	ci = models.TextField(blank=True, null=True)
	telefono = models.TextField(blank=True, null=True)
	ocupacion = models.TextField(blank=True, null=True)
	direccion = models.TextField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'tutores'

class UsuarioRoles(models.Model):
	id = models.UUIDField(primary_key=True)
	usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
	rol = models.ForeignKey(Roles, models.DO_NOTHING)
	asignado_por = models.ForeignKey('Usuarios', models.DO_NOTHING, db_column='asignado_por', related_name='usuarioroles_asignado_por_set')
	fecha_asignacion = models.DateTimeField(blank=True, null=True)
	activo = models.BooleanField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'usuario_roles'
		unique_together = (('usuario', 'rol'),)

class Usuarios(models.Model):
	id = models.UUIDField(primary_key=True)
	nombre = models.TextField()
	apellido = models.TextField()
	email = models.TextField(unique=True)
	password_hash = models.TextField()
	ci = models.TextField(unique=True)
	telefono = models.TextField(blank=True, null=True)
	activo = models.BooleanField(blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'usuarios'

class Horarios(models.Model):
	id = models.UUIDField(primary_key=True)
	asignacion = models.ForeignKey(DocenteAsignacion, models.DO_NOTHING)
	dia_semana = models.IntegerField()
	hora_inicio = models.TimeField()
	hora_fin = models.TimeField()
	aula = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		managed = True
		db_table = 'horarios'
		unique_together = (('asignacion', 'dia_semana', 'hora_inicio'),)
