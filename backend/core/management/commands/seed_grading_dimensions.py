from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import DimensionesEvaluacion


class Command(BaseCommand):
    help = "Seed the grading dimensions used by the grade grid"

    def handle(self, *args, **options):
        gestion = timezone.now().year
        dimensions = [
            {
                "nombre": "Ser",
                "puntaje_maximo": 10,
                "descripcion": "Actitudes y valores",
                "orden": 1,
            },
            {
                "nombre": "Saber",
                "puntaje_maximo": 45,
                "descripcion": "Conocimientos y teoría",
                "orden": 2,
            },
            {
                "nombre": "Hacer",
                "puntaje_maximo": 40,
                "descripcion": "Habilidades, práctica y producción",
                "orden": 3,
            },
            {
                "nombre": "Autoevaluación",
                "puntaje_maximo": 5,
                "descripcion": "Autoevaluación trimestral",
                "orden": 4,
            },
        ]

        created = 0
        updated = 0
        expected_names = set()

        for data in dimensions:
            expected_names.add(data["nombre"].strip().lower())
            defaults = {
                "puntaje_maximo": data["puntaje_maximo"],
                "descripcion": data["descripcion"],
                "activo": True,
                "orden": data["orden"],
                "gestion": gestion,
            }

            if data["nombre"] == "Autoevaluación":
                existing = DimensionesEvaluacion.objects.filter(gestion=gestion, nombre__iexact="Decidir").first()
                if existing is not None:
                    existing.nombre = data["nombre"]
                    existing.puntaje_maximo = data["puntaje_maximo"]
                    existing.descripcion = data["descripcion"]
                    existing.activo = True
                    existing.orden = data["orden"]
                    existing.gestion = gestion
                    existing.save()
                    updated += 1
                    continue

            obj, was_created = DimensionesEvaluacion.objects.get_or_create(
                nombre=data["nombre"],
                gestion=gestion,
                defaults={**defaults, "id": __import__("uuid").uuid4()},
            )
            if not was_created:
                for field, value in defaults.items():
                    setattr(obj, field, value)
                obj.save()
            if was_created:
                created += 1
            else:
                updated += 1

        extra_dimensions = DimensionesEvaluacion.objects.filter(gestion=gestion)
        for dimension in extra_dimensions:
            if (dimension.nombre or "").strip().lower() not in expected_names:
                dimension.activo = False
                dimension.save(update_fields=["activo"])

        self.stdout.write(self.style.SUCCESS(
            f"Dimensiones listas para la gestión {gestion}: {created} creadas, {updated} actualizadas"
        ))
