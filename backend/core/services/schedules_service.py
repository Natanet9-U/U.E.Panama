from datetime import datetime, time, timedelta
from django.db.models import Q
from ..models import Horarios, DocenteAsignacion, Docentes, Areas, Grados
from .access_service import AccessControlService


class SchedulesService:
    """Service layer for schedule management following SOLID principles."""

    def __init__(self):
        self.access_control = AccessControlService()

    def build_schedules_page(self, usuario, grado_id=None):
        """
        Build complete schedules page data including KPIs, calendar, and upcoming classes.
        
        Args:
            usuario: Authenticated user object
            grado_id: Optional grade filter
            
        Returns:
            dict with resumen, calendario, proximas_clases, and permisos
        """
        permisos = self.access_control.build_permissions_payload(usuario)
        
        # Get filtered schedule data based on user role
        schedules = self._get_filtered_schedules(usuario, grado_id)
        
        # Build aggregated data
        resumen = self._build_summary(schedules)
        calendario = self._build_calendar(schedules)
        proximas_clases = self._build_upcoming_classes(schedules)
        
        return {
            "resumen": resumen,
            "calendario": calendario,
            "proximas_clases": proximas_clases,
            "permisos": permisos,
        }

    def _get_filtered_schedules(self, usuario, grado_id=None):
        """Get schedules filtered by user role and optional grade."""
        puede_ver_todo = self.access_control.can_view_all_academic_data(usuario)
        
        schedules = Horarios.objects.select_related(
            'asignacion',
            'asignacion__docente',
            'asignacion__docente__usuario',
            'asignacion__grado',
            'asignacion__area'
        )
        
        if not puede_ver_todo:
            # Docentes see only their own schedules
            try:
                docente = Docentes.objects.get(usuario=usuario)
                schedules = schedules.filter(asignacion__docente=docente)
            except Docentes.DoesNotExist:
                schedules = schedules.none()
        
        if grado_id:
            schedules = schedules.filter(asignacion__grado_id=grado_id)
        
        return list(schedules.order_by('dia_semana', 'hora_inicio'))

    def _build_summary(self, schedules):
        """Build KPI summary cards."""
        if not schedules:
            return [
                {"titulo": "Clases/Semana", "valor": "0", "detalle": "Sin datos", "icono": "calendar", "acento": "slate"},
                {"titulo": "Horas Totales", "valor": "0h", "detalle": "Sin datos", "icono": "clock", "acento": "slate"},
                {"titulo": "Aulas", "valor": "0", "detalle": "Sin datos", "icono": "building", "acento": "slate"},
                {"titulo": "Promedio Diario", "valor": "0h", "detalle": "Sin datos", "icono": "users", "acento": "slate"},
            ]

        # Calculate total classes per week
        total_classes = len(schedules)
        
        # Calculate total hours
        total_minutes = 0
        unique_classrooms = set()
        for schedule in schedules:
            if schedule.hora_inicio and schedule.hora_fin:
                start = datetime.combine(datetime.today(), schedule.hora_inicio)
                end = datetime.combine(datetime.today(), schedule.hora_fin)
                duration = (end - start).total_seconds() / 60
                total_minutes += duration
            if schedule.aula:
                unique_classrooms.add(schedule.aula)
        
        total_hours = total_minutes / 60
        avg_daily_hours = total_hours / 5 if total_hours > 0 else 0  # Assume 5 school days
        
        return [
            {
                "titulo": "Clases/Semana",
                "valor": str(total_classes),
                "detalle": f"{total_classes} clases programadas",
                "icono": "calendar",
                "acento": "blue",
            },
            {
                "titulo": "Horas Totales",
                "valor": f"{total_hours:.1f}h",
                "detalle": f"Jornada completa",
                "icono": "clock",
                "acento": "violet",
            },
            {
                "titulo": "Aulas",
                "valor": str(len(unique_classrooms)),
                "detalle": f"{len(unique_classrooms)} aulas en uso",
                "icono": "building",
                "acento": "emerald",
            },
            {
                "titulo": "Promedio Diario",
                "valor": f"{avg_daily_hours:.1f}h",
                "detalle": f"Por día escolar",
                "icono": "users",
                "acento": "orange",
            },
        ]

    def _build_calendar(self, schedules):
        """Build weekly calendar grid with time slots."""
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        hours = self._get_school_hours()
        
        # Group schedules by day and hour
        schedule_map = {}
        for schedule in schedules:
            day_key = (schedule.dia_semana, schedule.hora_inicio)
            if day_key not in schedule_map:
                schedule_map[day_key] = []
            schedule_map[day_key].append(schedule)
        
        # Build calendar structure
        calendario = []
        for hour in hours:
            row = {"hora": hour.strftime("%H:%M"), "clases": {}}
            for day_num, day_name in enumerate(days):
                day_key = (day_num, hour)
                if day_key in schedule_map:
                    clases = schedule_map[day_key]
                    row["clases"][day_name] = [
                        self._format_class(cls) for cls in clases
                    ]
                else:
                    row["clases"][day_name] = []
            calendario.append(row)
        
        return calendario

    def _build_upcoming_classes(self, schedules):
        """Build list of upcoming classes for the next 7 days."""
        today = datetime.today()
        upcoming = []
        
        # Map day numbers to dates
        day_offsets = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 2, 6: 1}  # Next occurrence
        
        for schedule in schedules[:10]:  # Limit to 10 upcoming
            day_offset = day_offsets.get(schedule.dia_semana, 0)
            class_date = today + timedelta(days=day_offset)
            
            upcoming.append({
                "fecha": class_date.strftime("%d %b"),
                "dia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][
                    class_date.weekday()
                ],
                "hora": schedule.hora_inicio.strftime("%H:%M") if schedule.hora_inicio else "N/A",
                "asignatura": schedule.asignacion.area.nombre if schedule.asignacion else "N/A",
                "grado": f"{schedule.asignacion.grado.nivel}{schedule.asignacion.grado.numero}{schedule.asignacion.grado.paralelo}"
                if schedule.asignacion else "N/A",
                "aula": schedule.aula or "N/A",
                "docente": schedule.asignacion.docente.usuario.nombre if schedule.asignacion else "N/A",
            })
        
        return upcoming

    def _format_class(self, schedule):
        """Format a single class for display."""
        return {
            "asignatura": schedule.asignacion.area.nombre if schedule.asignacion else "N/A",
            "grado": f"{schedule.asignacion.grado.nivel}{schedule.asignacion.grado.numero}{schedule.asignacion.grado.paralelo}"
            if schedule.asignacion else "N/A",
            "aula": schedule.aula or "N/A",
            "docente": schedule.asignacion.docente.usuario.nombre if schedule.asignacion else "N/A",
            "estudiantes": self._count_students(schedule.asignacion) if schedule.asignacion else 0,
            "hora_fin": schedule.hora_fin.strftime("%H:%M") if schedule.hora_fin else "N/A",
        }

    def _count_students(self, asignacion):
        """Count students in a class assignment."""
        from ..models import Estudiantes
        if not asignacion:
            return 0
        return Estudiantes.objects.filter(grado=asignacion.grado).count()

    def _get_school_hours(self):
        """Get list of school hours."""
        hours = []
        start_hour = 8
        end_hour = 16
        for hour in range(start_hour, end_hour):
            hours.append(time(hour, 0))
        return hours
