from uuid import uuid4
import re
import unicodedata

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import Docentes, Roles, UsuarioRoles, Usuarios
from .access_service import AccessControlService


class DocentesService:
    def __init__(self):
        self.access_service = AccessControlService()

    def build_docentes_page(self, usuario, *, query=None, page=1, page_size=8):
        queryset = Docentes.objects.select_related("usuario").order_by("usuario__nombre", "usuario__apellido")
        if not self.access_service.can_create_academic_data(usuario):
            queryset = queryset.none()

        if query:
            queryset = queryset.filter(
                Q(usuario__nombre__icontains=query)
                | Q(usuario__apellido__icontains=query)
                | Q(usuario__email__icontains=query)
                | Q(usuario__ci__icontains=query)
                | Q(especialidad__icontains=query)
                | Q(titulo_academico__icontains=query)
            )

        total = queryset.count()
        page = max(int(page or 1), 1)
        page_size = max(min(int(page_size or 8), 24), 1)
        offset = (page - 1) * page_size

        docentes = [self._serialize_docente(docente) for docente in queryset[offset : offset + page_size]]

        return {
            "docentes": docentes,
            "paginacion": {
                "pagina": page,
                "tamano": page_size,
                "total": total,
                "paginas": max((total + page_size - 1) // page_size, 1),
                "siguiente": page * page_size < total,
                "anterior": page > 1,
            },
            "permisos": self.access_service.build_permissions_payload(usuario),
        }

    def create_docente(self, usuario, data):
        if not self.access_service.can_create_academic_data(usuario):
            raise PermissionError("No tienes permisos para crear docentes")

        nombres = (data.get("nombres") or "").strip()
        apellido = (data.get("apellido") or data.get("primer_apellido") or "").strip()
        segundo_apellido = (data.get("segundo_apellido") or "").strip() or None
        ci = (data.get("ci") or "").strip() or None
        telefono = (data.get("telefono") or "").strip() or None
        titulo_academico = (data.get("titulo_academico") or "").strip() or None
        especialidad = (data.get("especialidad") or "").strip() or None

        if not nombres or not apellido:
            raise ValueError("Debes enviar nombres y apellido")

        with transaction.atomic():
            email = self._build_unique_email(nombres, apellido)
            temp_password = self._build_temp_password(nombres, apellido)

            if ci and Usuarios.objects.filter(ci__iexact=ci).exists():
                raise ValueError("Ya existe un usuario con ese CI")

            usuario_docente = Usuarios.objects.create(
                id=uuid4(),
                nombre=nombres,
                apellido=apellido,
                email=email,
                password_hash=make_password(temp_password),
                ci=ci or self._build_unique_ci(nombres, apellido),
                telefono=telefono,
                activo=True,
                created_at=timezone.now(),
            )

            docente = Docentes.objects.create(
                id=uuid4(),
                usuario=usuario_docente,
                titulo_academico=titulo_academico,
                especialidad=especialidad,
                fecha_ingreso_institucion=timezone.now().date(),
                anos_experiencia=data.get("anos_experiencia") or None,
            )

            self._assign_teacher_role(usuario_docente, usuario)

        return {
            "id": str(docente.id),
            "nombre": f"{nombres} {apellido}".strip(),
            "email": email,
            "usuario_temporal": temp_password,
            "mensaje": f"Docente creado exitosamente con usuario {email}",
        }

    def _assign_teacher_role(self, usuario_creado, assigned_by):
        role = Roles.objects.filter(nombre__iexact="docente").first()
        if role is None:
            return

        UsuarioRoles.objects.get_or_create(
            usuario=usuario_creado,
            rol=role,
            defaults={
                "asignado_por": assigned_by,
                "fecha_asignacion": timezone.now(),
                "activo": True,
            },
        )

    def _build_unique_email(self, nombres, apellido):
        base = self._slugify(f"{nombres}.{apellido}")
        base = base or "docente"

        for _ in range(10):
            email = f"{base}.{uuid4().hex[:6]}@uepanama"
            if not Usuarios.objects.filter(email__iexact=email).exists():
                return email

        return f"{base}.{uuid4().hex[:12]}@uepanama"

    def _build_unique_ci(self, nombres, apellido):
        return f"DOC-{self._slugify(nombres)[:3].upper()}{self._slugify(apellido)[:3].upper()}-{uuid4().hex[:6].upper()}"

    def _build_temp_password(self, nombres, apellido):
        base = self._slugify(f"{nombres}{apellido}")
        return f"{base[:4] or 'doc'}{uuid4().hex[:6]}"

    def _slugify(self, value):
        normalized = unicodedata.normalize("NFKD", str(value or ""))
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"[^a-zA-Z0-9]+", ".", normalized).strip(".").lower()
        return re.sub(r"\.+", ".", normalized)

    def _serialize_docente(self, docente):
        usuario = docente.usuario
        return {
            "id": str(docente.id),
            "nombre": f"{usuario.nombre} {usuario.apellido}".strip(),
            "email": usuario.email,
            "ci": usuario.ci,
            "telefono": usuario.telefono or "-",
            "titulo_academico": docente.titulo_academico or "-",
            "especialidad": docente.especialidad or "-",
            "activo": bool(usuario.activo),
        }