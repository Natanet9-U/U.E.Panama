from django.db import migrations, models


def copy_ci_to_rude(apps, schema_editor):
    Estudiantes = apps.get_model("core", "Estudiantes")
    for estudiante in Estudiantes.objects.all():
        if not estudiante.rude and estudiante.ci:
            estudiante.rude = estudiante.ci
            estudiante.save(update_fields=["rude"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_create_horarios_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="estudiantes",
            name="rude",
            field=models.TextField(blank=True, null=True, unique=True),
        ),
        migrations.RunPython(copy_ci_to_rude, migrations.RunPython.noop),
    ]