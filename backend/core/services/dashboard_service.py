from datetime import datetime, timedelta
from collections import Counter

from django.db.models import Avg
from django.utils import timezone

from ..models import Asistencias, DocenteAsignacion, Estudiantes, Licencias, Notas, Periodos


class DashboardService:
    def build_dashboard(self, usuario):
        periodo_activo = self._get_periodo_activo()
        return {
            "resumen": self._build_summary(periodo_activo),
            "asistencia_semanal": self._build_weekly_attendance(),
            "promedio_por_asignatura": self._build_subject_averages(periodo_activo),
            "rendimiento": self._build_performance_distribution(periodo_activo),
            "proximas_clases": self._build_upcoming_classes(usuario),
            "actividad_reciente": self._build_recent_activity(),
            "tareas_pendientes": self._build_pending_tasks(periodo_activo),
            "estudiantes_destacados": self._build_highlight_students(periodo_activo),
            "periodo_activo": self._format_period(periodo_activo),
        }

    def _get_periodo_activo(self):
        periodo = Periodos.objects.filter(activo=True).order_by("-gestion", "-numero").first()
        if periodo is not None:
            return periodo

        return Periodos.objects.order_by("-gestion", "-numero").first()

    def _build_summary(self, periodo_activo):
        total_estudiantes = Estudiantes.objects.count()
        total_asignaciones = DocenteAsignacion.objects.count()

        notas_qs = Notas.objects.exclude(total__isnull=True)
        if periodo_activo is not None:
            notas_qs = notas_qs.filter(periodo=periodo_activo)

        promedio_general = notas_qs.aggregate(promedio=Avg("total"))["promedio"] or 0

        hoy = timezone.localdate()
        asistencias_hoy = Asistencias.objects.filter(fecha=hoy)
        presentes_hoy = asistencias_hoy.exclude(estado__iexact="Falta").exclude(estado__iexact="Ausente").count()
        porcentaje_asistencia = round((presentes_hoy / total_estudiantes) * 100) if total_estudiantes else 0

        return [
            {
                "titulo": "Total Estudiantes",
                "valor": str(total_estudiantes),
                "detalle": self._growth_text(total_estudiantes, "estudiantes registrados"),
                "acento": "blue",
            },
            {
                "titulo": "Cursos Activos",
                "valor": str(total_asignaciones),
                "detalle": self._growth_text(total_asignaciones, "asignaciones académicas"),
                "acento": "violet",
            },
            {
                "titulo": "Promedio General",
                "valor": f"{promedio_general:.1f}",
                "detalle": self._period_comparison(periodo_activo),
                "acento": "green",
            },
            {
                "titulo": "Asistencia Hoy",
                "valor": f"{porcentaje_asistencia}%",
                "detalle": f"{presentes_hoy} de {total_estudiantes} estudiantes presentes",
                "acento": "orange",
            },
        ]

    def _build_weekly_attendance(self):
        hoy = timezone.localdate()
        inicio = hoy - timedelta(days=4)
        fechas = [inicio + timedelta(days=offset) for offset in range(5)]
        labels = [self._weekday_label(fecha) for fecha in fechas]

        data = []
        for fecha in fechas:
            asistencias = Asistencias.objects.filter(fecha=fecha)
            presentes = asistencias.exclude(estado__iexact="Falta").exclude(estado__iexact="Ausente").count()
            total = asistencias.count()
            porcentaje = round((presentes / total) * 100) if total else 0
            data.append(porcentaje)

        return {"labels": labels, "data": data}

    def _build_subject_averages(self, periodo_activo):
        notas_qs = Notas.objects.filter(total__isnull=False).select_related("asignacion__area")
        if periodo_activo is not None:
            notas_qs = notas_qs.filter(periodo=periodo_activo)

        aggregation = (
            notas_qs.values("asignacion__area__nombre")
            .annotate(promedio=Avg("total"))
            .order_by("asignacion__area__nombre")
        )

        labels = []
        data = []
        for item in aggregation:
            nombre = item["asignacion__area__nombre"] or "Sin asignatura"
            labels.append(nombre)
            data.append(round(item["promedio"] or 0, 1))

        return {"labels": labels, "data": data}

    def _build_performance_distribution(self, periodo_activo):
        notas_qs = Notas.objects.filter(total__isnull=False).select_related("estudiante")
        if periodo_activo is not None:
            notas_qs = notas_qs.filter(periodo=periodo_activo)

        promedios = (
            notas_qs.values("estudiante_id", "estudiante__nombres", "estudiante__primer_apellido")
            .annotate(promedio=Avg("total"))
            .order_by("-promedio")
        )

        buckets = Counter({"Excelente": 0, "Bueno": 0, "Regular": 0, "Deficiente": 0})
        for item in promedios:
            promedio = float(item["promedio"] or 0)
            if promedio >= 90:
                buckets["Excelente"] += 1
            elif promedio >= 75:
                buckets["Bueno"] += 1
            elif promedio >= 60:
                buckets["Regular"] += 1
            else:
                buckets["Deficiente"] += 1

        total = sum(buckets.values())
        if total == 0:
            return [
                {"label": "Excelente", "value": 0},
                {"label": "Bueno", "value": 0},
                {"label": "Regular", "value": 0},
                {"label": "Deficiente", "value": 0},
            ]

        return [
            {"label": label, "value": round((value / total) * 100)}
            for label, value in buckets.items()
        ]

    def _build_upcoming_classes(self, usuario):
        asignaciones = DocenteAsignacion.objects.select_related("docente__usuario", "grado", "area").order_by("grado__gestion", "grado__numero", "area__nombre")
        if usuario is not None:
            usuario_asignaciones = asignaciones.filter(docente__usuario=usuario)
            if usuario_asignaciones.exists():
                asignaciones = usuario_asignaciones

        items = []
        for asignacion in asignaciones[:3]:
            items.append(
                {
                    "titulo": f"{asignacion.area.nombre}",
                    "detalle": f"{asignacion.grado.nivel} {asignacion.grado.numero}{asignacion.grado.paralelo}",
                    "subdetalle": "Horario por definir",
                    "estudiantes": self._count_students_for_grade(asignacion.grado_id),
                }
            )
        return items

    def _build_recent_activity(self):
        activities = []

        for asistencia in Asistencias.objects.select_related("estudiante__usuario").order_by("-fecha")[:4]:
            estudiante = asistencia.estudiante
            nombre = f"{estudiante.nombres} {estudiante.primer_apellido}".strip()
            timestamp = datetime.combine(asistencia.fecha, datetime.min.time())
            activities.append(
                (
                    timestamp,
                    {
                        "persona": nombre,
                        "detalle": f"Registró asistencia como {asistencia.estado}",
                        "tiempo": self._relative_time(asistencia.fecha),
                        "estado": "ok" if self._is_positive_state(asistencia.estado) else "warning",
                    },
                )
            )

        for nota in Notas.objects.select_related("estudiante", "asignacion__area").filter(total__isnull=False).order_by("-updated_at", "-created_at")[:4]:
            estudiante = nota.estudiante
            nombre = f"{estudiante.nombres} {estudiante.primer_apellido}".strip()
            materia = nota.asignacion.area.nombre if nota.asignacion and nota.asignacion.area else "Asignatura"
            timestamp = nota.updated_at or nota.created_at or timezone.now()
            activities.append(
                (
                    timestamp,
                    {
                        "persona": nombre,
                        "detalle": f"Obtuvo {nota.total} en {materia}",
                        "tiempo": self._relative_time(timestamp),
                        "estado": "ok" if (nota.total or 0) >= 70 else "warning",
                    },
                )
            )

        for licencia in Licencias.objects.select_related("estudiante").order_by("-created_at")[:2]:
            estudiante = licencia.estudiante
            nombre = f"{estudiante.nombres} {estudiante.primer_apellido}".strip()
            timestamp = licencia.created_at or timezone.now()
            activities.append(
                (
                    timestamp,
                    {
                        "persona": nombre,
                        "detalle": "Solicitó una licencia académica",
                        "tiempo": self._relative_time(timestamp),
                        "estado": "warning" if licencia.aprobado is False else "ok",
                    },
                )
            )

        activities.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in activities[:4]]

    def _build_pending_tasks(self, periodo_activo):
        notas_pendientes = Notas.objects.filter(total__isnull=True)
        if periodo_activo is not None:
            notas_pendientes = notas_pendientes.filter(periodo=periodo_activo)

        cantidad = notas_pendientes.count()
        dias_restantes = None
        if periodo_activo is not None and periodo_activo.fecha_fin:
            dias_restantes = max((periodo_activo.fecha_fin - timezone.localdate()).days, 0)

        return {
            "cantidad": cantidad,
            "mensaje": (
                f"Tienes {cantidad} tareas pendientes de revisión y calificación."
                if cantidad
                else "No tienes tareas pendientes de revisión por ahora."
            ),
            "detalle": (
                f"La fecha límite es en {dias_restantes} días." if dias_restantes is not None else "Revisa las notas pendientes antes del cierre del periodo."
            ),
        }

    def _build_highlight_students(self, periodo_activo):
        notas_qs = Notas.objects.filter(total__isnull=False).select_related("estudiante__usuario")
        if periodo_activo is not None:
            notas_qs = notas_qs.filter(periodo=periodo_activo)

        top_students = (
            notas_qs.values("estudiante_id", "estudiante__nombres", "estudiante__primer_apellido")
            .annotate(promedio=Avg("total"))
            .order_by("-promedio")[:5]
        )

        items = []
        for item in top_students:
            nombre = f"{item['estudiante__nombres']} {item['estudiante__primer_apellido']}".strip()
            promedio = round(float(item["promedio"] or 0), 1)
            items.append(
                {
                    "nombre": nombre,
                    "promedio": promedio,
                    "mensaje": "Rendimiento sobresaliente este mes" if promedio >= 90 else "Buen desempeño académico",
                }
            )
        return items

    def _count_students_for_grade(self, grado_id):
        return Estudiantes.objects.filter(grado_id=grado_id).count()

    def _format_period(self, periodo_activo):
        if periodo_activo is None:
            return None
        return {
            "nombre": periodo_activo.nombre,
            "numero": periodo_activo.numero,
            "gestion": periodo_activo.gestion,
        }

    def _weekday_label(self, fecha):
        labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        return labels[fecha.weekday()]

    def _growth_text(self, value, noun):
        return f"{value} {noun}"

    def _period_comparison(self, periodo_activo):
        if periodo_activo is None:
            return "Promedio calculado con los registros disponibles"
        return f"{periodo_activo.nombre} {periodo_activo.gestion}"

    def _relative_time(self, value):
        if value is None:
            return "Hace un momento"

        if hasattr(value, "date"):
            delta = timezone.localdate() - value.date()
        else:
            delta = timezone.localdate() - value

        days = max(delta.days, 0)
        if days == 0:
            return "Hoy"
        if days == 1:
            return "Hace 1 día"
        return f"Hace {days} días"

    def _is_positive_state(self, estado):
        estado_normalizado = (estado or "").strip().lower()
        return estado_normalizado not in {"falta", "ausente", "inasistencia"}
