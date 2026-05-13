from uuid import uuid4
from django.db import transaction
from django.utils import timezone

from ..models import Estudiantes, Usuarios, Grados, DocenteAsignacion, Areas, Notas, Periodos
from .access_service import AccessControlService


class EnrollmentService:
    """Service layer for student enrollment and re-enrollment."""

    def __init__(self):
        self.access_service = AccessControlService()

    def search_existing_student(self, ci):
        """
        Search for a student by CI (exact match).
        Returns student data if found, None otherwise.
        """
        try:
            estudiante = Estudiantes.objects.select_related("usuario", "grado").get(ci=ci)
            return {
                "id": str(estudiante.id),
                "ci": estudiante.ci,
                "nombre": f"{estudiante.nombres} {estudiante.primer_apellido}".strip(),
                "nombres": estudiante.nombres,
                "primer_apellido": estudiante.primer_apellido,
                "segundo_apellido": estudiante.segundo_apellido or "",
                "grado_actual_id": str(estudiante.grado.id) if estudiante.grado else None,
                "grado_actual_nombre": f"{estudiante.grado.nivel} {estudiante.grado.numero}{estudiante.grado.paralelo}" if estudiante.grado else None,
                "activo": bool(estudiante.usuario.activo),
            }
        except Estudiantes.DoesNotExist:
            return None

    def enroll_new_student(self, usuario, data):
        """
        Enroll a new student.
        
        Args:
            usuario: Authenticated user (must be director/secretaria)
            data: dict with:
                - nombres: str (required)
                - primer_apellido: str (required)
                - segundo_apellido: str (optional)
                - ci: str (required, must be unique)
                - fecha_nacimiento: str YYYY-MM-DD (optional)
                - genero: str M/F (optional)
                - grado_id: str (required)
                - tutor_id: str (optional)
        
        Returns:
            dict with enrolled student data
        """
        if not self.access_service.can_create_academic_data(usuario):
            raise PermissionError("No tienes permisos para inscribir estudiantes")

        ci = data.get("ci", "").strip()
        if not ci or not data.get("nombres") or not data.get("primer_apellido") or not data.get("grado_id"):
            raise ValueError("Debes enviar ci, nombres, primer_apellido y grado_id")

        # Check if CI already exists
        if Estudiantes.objects.filter(ci=ci).exists():
            existing = self.search_existing_student(ci)
            if existing["activo"]:
                raise ValueError(f"El estudiante con CI {ci} ya está inscrito en el sistema")
            else:
                return self.re_enroll_existing_student(usuario, ci, data.get("grado_id"))

        try:
            grado = Grados.objects.get(id=data.get("grado_id"))
        except Grados.DoesNotExist as exc:
            raise ValueError("El grado seleccionado no existe") from exc

        with transaction.atomic():
            # Create usuario
            usuario_estudiante = Usuarios.objects.create(
                id=uuid4(),
                nombre=data.get("nombres", ""),
                apellido=data.get("primer_apellido", ""),
                email=f"est_{uuid4()}@uepa nama.edu",
                password_hash="",
                ci=ci,
                activo=True,
            )

            # Create estudiante
            estudiante = Estudiantes.objects.create(
                id=uuid4(),
                usuario=usuario_estudiante,
                nombres=data.get("nombres", ""),
                primer_apellido=data.get("primer_apellido", ""),
                segundo_apellido=data.get("segundo_apellido", "") or None,
                ci=ci,
                grado=grado,
                fecha_nacimiento=data.get("fecha_nacimiento") or None,
                genero=data.get("genero") or None,
                tutor_id=data.get("tutor_id") or None,
            )

            # Add to all areas of the grade
            self._add_student_to_grade_areas(estudiante, grado)

        return {
            "id": str(estudiante.id),
            "ci": estudiante.ci,
            "nombre": f"{estudiante.nombres} {estudiante.primer_apellido}".strip(),
            "grado": f"{grado.nivel} {grado.numero}{grado.paralelo}",
            "mensaje": f"Estudiante {estudiante.nombres} inscrito exitosamente en {grado.nivel} {grado.numero}{grado.paralelo}",
        }

    def re_enroll_existing_student(self, usuario, ci, new_grado_id):
        """
        Re-enroll an existing inactive student in a new grade.
        
        Args:
            usuario: Authenticated user (must be director/secretaria)
            ci: Student CI to re-enroll
            new_grado_id: New grade ID for re-enrollment
        
        Returns:
            dict with re-enrolled student data
        """
        if not self.access_service.can_create_academic_data(usuario):
            raise PermissionError("No tienes permisos para inscribir estudiantes")

        try:
            estudiante = Estudiantes.objects.select_related("usuario", "grado").get(ci=ci)
        except Estudiantes.DoesNotExist as exc:
            raise ValueError("Estudiante no encontrado") from exc

        if estudiante.usuario.activo:
            raise ValueError(f"El estudiante {estudiante.nombres} ya está activo. No se puede reinscribir.")

        try:
            new_grado = Grados.objects.get(id=new_grado_id)
        except Grados.DoesNotExist as exc:
            raise ValueError("El grado seleccionado no existe") from exc

        # Capture old grado name before updating
        old_grado_nombre = f"{estudiante.grado.nivel}" if estudiante.grado else "Desconocido"

        with transaction.atomic():
            # Reactivate usuario
            estudiante.usuario.activo = True
            estudiante.usuario.save(update_fields=["activo"])

            # Update grado
            estudiante.grado = new_grado
            estudiante.save(update_fields=["grado"])

            # Add to all areas of the new grade
            self._add_student_to_grade_areas(estudiante, new_grado)

        return {
            "id": str(estudiante.id),
            "ci": estudiante.ci,
            "nombre": f"{estudiante.nombres} {estudiante.primer_apellido}".strip(),
            "grado_anterior": old_grado_nombre,
            "grado_nuevo": f"{new_grado.nivel} {new_grado.numero}{new_grado.paralelo}",
            "mensaje": f"Estudiante {estudiante.nombres} reinscrito exitosamente en {new_grado.nivel} {new_grado.numero}{new_grado.paralelo}",
        }

    def _add_student_to_grade_areas(self, estudiante, grado):
        """
        Add a student to all courses (asignaciones) of a grade by creating Notas records.
        This allows grades to be entered for the student in each course.
        """
        # Get all DocenteAsignacion (courses) for this grade
        asignaciones = DocenteAsignacion.objects.filter(grado=grado).select_related("area")
        
        # Get current/active period
        try:
            periodo = Periodos.objects.filter(activo=True).first()
            if not periodo:
                # Fallback to most recent period
                periodo = Periodos.objects.order_by("-fecha_inicio").first()
            if not periodo:
                return  # No period available, skip
        except Exception:
            return  # Period query failed, skip
        
        # Create Notas records for each asignacion
        for asignacion in asignaciones:
            # Check if this Nota already exists
            if not Notas.objects.filter(
                estudiante=estudiante,
                asignacion=asignacion,
                periodo=periodo
            ).exists():
                Notas.objects.create(
                    id=uuid4(),
                    estudiante=estudiante,
                    asignacion=asignacion,
                    periodo=periodo,
                    total=0,
                )

    def get_enrollment_catalogs(self, usuario):
        """
        Get catalogs needed for enrollment: grades, tutores.
        Only director/secretaria can access.
        """
        if not self.access_service.can_create_academic_data(usuario):
            return {"grados": [], "tutores": []}

        grados = [
            {"id": str(g.id), "nombre": f"{g.nivel} {g.numero}{g.paralelo}"}
            for g in Grados.objects.order_by("gestion", "nivel", "numero", "paralelo")
        ]

        from ..models import Tutores
        tutores = [
            {"id": str(t.id), "nombre": f"{t.nombre} {t.apellido}".strip()}
            for t in Tutores.objects.order_by("nombre")
        ]

        return {
            "grados": grados,
            "tutores": tutores,
        }
