import unicodedata

from ..models import DocenteAsignacion, UsuarioRoles


class AccessControlService:
    DIRECT_ROLES = {"director", "secretaria"}

    def get_role_names(self, usuario):
        if usuario is None:
            return set()

        roles = UsuarioRoles.objects.filter(usuario=usuario, activo=True).select_related("rol")
        return {self._normalize_role(assignment.rol.nombre) for assignment in roles}

    def can_view_all_academic_data(self, usuario):
        return bool(self.get_role_names(usuario) & self.DIRECT_ROLES)

    def can_create_academic_data(self, usuario):
        return self.can_view_all_academic_data(usuario)

    def filter_students_queryset(self, queryset, usuario):
        if self.can_view_all_academic_data(usuario):
            return queryset

        grade_ids = self.get_assigned_grade_ids(usuario)
        if not grade_ids:
            return queryset.none()

        return queryset.filter(grado_id__in=grade_ids)

    def filter_courses_queryset(self, queryset, usuario):
        if self.can_view_all_academic_data(usuario):
            return queryset

        return queryset.filter(docente__usuario=usuario)

    def filter_notes_queryset(self, queryset, usuario):
        if self.can_view_all_academic_data(usuario):
            return queryset

        return queryset.filter(asignacion__docente__usuario=usuario)

    def get_assigned_grade_ids(self, usuario):
        if usuario is None:
            return []

        return list(
            DocenteAsignacion.objects.filter(docente__usuario=usuario)
            .values_list("grado_id", flat=True)
            .distinct()
        )

    def get_assigned_assignment_ids(self, usuario):
        if usuario is None:
            return []

        return list(
            DocenteAsignacion.objects.filter(docente__usuario=usuario)
            .values_list("id", flat=True)
            .distinct()
        )

    def build_permissions_payload(self, usuario):
        role_names = sorted(self.get_role_names(usuario))
        return {
            "roles": role_names,
            "puede_ver_todo": self.can_view_all_academic_data(usuario),
            "puede_crear": self.can_create_academic_data(usuario),
        }

    def _normalize_role(self, value):
        normalized = unicodedata.normalize("NFKD", str(value or ""))
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        return normalized.strip().lower()
