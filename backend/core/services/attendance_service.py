from uuid import uuid4

from django.db import transaction
from django.utils import timezone

from ..models import Asistencias, DocenteAsignacion, Estudiantes, Licencias
from .access_service import AccessControlService


class AttendanceService:
    def __init__(self):
        self.access = AccessControlService()

    def mark_attendance(self, usuario, asignacion_id, fecha, estados_map):
        """
        Registrar asistencias para una asignación (curso) en una fecha.
        `estados_map` debe ser {estudiante_id: estado}
        Los docentes pueden marcar solo sus asignaciones; secretaria/director pueden marcar cualquier asignación.
        """
        assignment_ids = self.access.get_assigned_assignment_ids(usuario)
        puede_marcar = self.access.can_view_all_academic_data(usuario) or (asignacion_id in assignment_ids)
        if not puede_marcar:
            raise PermissionError("No tienes permisos para registrar asistencia en esa asignación")

        created = []
        with transaction.atomic():
            for estudiante_id, estado in (estados_map or {}).items():
                obj, _ = Asistencias.objects.update_or_create(
                    estudiante_id=estudiante_id,
                    fecha=fecha,
                    defaults={
                        "id": uuid4(),
                        "registrado_por": usuario,
                        "estado": estado,
                        "created_at": timezone.now(),
                    },
                )
                created.append(obj)

        return [str(a.id) for a in created]

    def create_licencia(self, usuario, data):
        """
        Crear una licencia académica para un estudiante. Solo roles directivos (director/secretaria) pueden crearla.
        Espera: estudiante_id, fecha_inicio, fecha_fin, motivo (opcional), requiere_certificado (bool).
        """
        if not self.access.can_create_academic_data(usuario):
            raise PermissionError("No tienes permisos para crear licencias")

        estudiante_id = data.get("estudiante_id")
        fecha_inicio = data.get("fecha_inicio")
        fecha_fin = data.get("fecha_fin")
        motivo = data.get("motivo")
        requiere = bool(data.get("requiere_certificado", False))

        if not estudiante_id or not fecha_inicio or not fecha_fin:
            raise ValueError("Faltan datos: estudiante_id, fecha_inicio o fecha_fin")

        licencia = Licencias.objects.create(
            id=uuid4(),
            estudiante_id=estudiante_id,
            solicitado_por=usuario,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            motivo=motivo,
            requiere_certificado=requiere,
            aprobado=True,
            aprobado_por=usuario,
            created_at=timezone.now(),
        )

        return {"id": str(licencia.id)}
