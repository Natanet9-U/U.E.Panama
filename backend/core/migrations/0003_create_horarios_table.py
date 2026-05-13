from django.db import migrations


CREATE_HORARIOS_TABLE = """
CREATE TABLE IF NOT EXISTS horarios (
    id uuid PRIMARY KEY,
    dia_semana integer NOT NULL,
    hora_inicio time NOT NULL,
    hora_fin time NOT NULL,
    aula text NULL,
    created_at timestamp with time zone NULL,
    asignacion_id uuid NOT NULL REFERENCES docente_asignacion(id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT horarios_asignacion_id_dia_semana_hora_inicio_uniq UNIQUE (asignacion_id, dia_semana, hora_inicio)
);
"""


DROP_HORARIOS_TABLE = "DROP TABLE IF EXISTS horarios CASCADE;"


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_actividades_actividadnotas"),
    ]

    operations = [
        migrations.RunSQL(CREATE_HORARIOS_TABLE, reverse_sql=DROP_HORARIOS_TABLE),
    ]