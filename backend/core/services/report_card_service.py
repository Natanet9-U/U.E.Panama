from django.db import connection
from ..models import Estudiantes, Inscripciones, NotaObservaciones, Asistencias, Periodos, DocenteAsignacion
from ..tracing import trace_service_class
from .access_service import AccessControlService


@trace_service_class
class ReportCardService:

    def __init__(self):
        self.ac = AccessControlService()

    def _nota_total_periodo(self, estudiante_id, docente_asignacion_id, periodo_id):
        """Retorna la nota total para un (estudiante, DA, periodo) usando v_notas_totales."""
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT nota_total FROM v_notas_totales
                   WHERE estudiante_id = %s AND docente_asignacion_id = %s AND periodo_id = %s""",
                [estudiante_id, docente_asignacion_id, periodo_id],
            )
            row = cursor.fetchone()
        return float(row[0]) if row and row[0] else None

    def generar_boletin(self, usuario, estudiante_id, gestion=None):
        estudiante_id = int(estudiante_id)
        # Verificar permisos: puede ver todo o es tutor del estudiante
        estudiantes_autorizados = self.ac.get_estudiantes_autorizados(usuario)
        if estudiantes_autorizados is not None and estudiante_id not in estudiantes_autorizados:
            raise PermissionError('No autorizado')

        estudiante = Estudiantes.objects.get(id=estudiante_id)

        if not gestion:
            ins_qs = Inscripciones.objects.filter(estudiante_id=estudiante_id)
            if hasattr(ins_qs, 'order_by'):
                ins_qs = ins_qs.order_by('-gestion')
            if hasattr(ins_qs, 'first'):
                inscripcion_actual = ins_qs.first()
            else:
                inscripcion_actual = ins_qs[0] if ins_qs else None
            if not inscripcion_actual:
                raise ValueError('sin inscripciones')
            gestion = inscripcion_actual.gestion

        inscripciones = Inscripciones.objects.filter(
            estudiante_id=estudiante_id, gestion=gestion
        )
        if hasattr(inscripciones, 'select_related'):
            inscripciones = inscripciones.select_related('curso__grado', 'curso__paralelo')

        if not inscripciones:
            raise ValueError(f'No hay inscripciones para la gestion {gestion}')

        periodos = Periodos.objects.filter(gestion=gestion).order_by('fecha_inicio')
        if hasattr(inscripciones, 'first'):
            curso = inscripciones.first().curso
        else:
            curso = inscripciones[0].curso

        asignaciones = DocenteAsignacion.objects.filter(
            curso=curso, gestion=gestion, activo=True
        ).select_related('area')

        from collections import OrderedDict
        materias_map = OrderedDict()
        for da in asignaciones:
            area_id = da.area_id
            if area_id not in materias_map:
                materias_map[area_id] = {
                    'docente_asignacion_id': da.id,
                    'area_id': area_id,
                    'area': da.area.nombre,
                    'docente': da.usuario.nombre_completo,
                    'notas_por_periodo': {},
                }

        for da in asignaciones:
            entry = materias_map[da.area_id]
            for p in periodos:
                pid_str = str(p.id)
                if pid_str in entry['notas_por_periodo']:
                    continue
                nota = self._nota_total_periodo(estudiante_id, da.id, p.id)
                if nota is not None:
                    entry['notas_por_periodo'][pid_str] = nota

        materias = []
        for entry in materias_map.values():
            notas_por_periodo = {}
            for p in periodos:
                pid_str = str(p.id)
                notas_por_periodo[pid_str] = entry['notas_por_periodo'].get(pid_str)

            notas_con_cero = [v if v is not None else 0 for v in notas_por_periodo.values()]
            materias.append({
                'docente_asignacion_id': entry['docente_asignacion_id'],
                'area_id': entry['area_id'],
                'area': entry['area'],
                'docente': entry['docente'],
                'notas_por_periodo': notas_por_periodo,
                'promedio_final': round(sum(notas_con_cero) / len(notas_con_cero), 2) if periodos else None,
            })

        observaciones = []
        for ins in inscripciones:
            for da in asignaciones:
                obs = NotaObservaciones.objects.filter(
                    estudiante_id=estudiante_id,
                    docente_asignacion=da,
                    periodo__in=periodos,
                )
                for o in obs:
                    observaciones.append({
                        'periodo_id': o.periodo_id,
                        'periodo': o.periodo.nombre,
                        'area': da.area.nombre,
                        'indicador': o.indicador,
                        'observacion': o.observacion or '',
                    })

        asistencias = []
        for p in periodos:
            total_asist = Asistencias.objects.filter(
                estudiante_id=estudiante_id,
                docente_asignacion__in=asignaciones,
                fecha__gte=p.fecha_inicio,
                fecha__lte=p.fecha_fin,
            )
            total = total_asist.count()
            presentes = total_asist.filter(estado='presente').count()
            asistencias.append({
                'periodo_id': p.id,
                'periodo': p.nombre,
                'total': total,
                'presentes': presentes,
                'porcentaje': round((presentes / total) * 100, 1) if total > 0 else 0,
            })

        return {
            'estudiante': {
                'id': estudiante.id,
                'rude': estudiante.rude,
                'ci': estudiante.ci,
                'nombres': estudiante.nombres,
                'primer_apellido': estudiante.primer_apellido,
                'segundo_apellido': estudiante.segundo_apellido or '',
            },
            'curso': {
                'id': curso.id,
                'nombre': str(curso),
                'grado': curso.grado.nombre,
                'paralelo': curso.paralelo.nombre,
            },
            'gestion': gestion,
            'periodos': [{'id': p.id, 'nombre': p.nombre} for p in periodos],
            'materias': materias,
            'observaciones': observaciones,
            'asistencias': asistencias,
        }

    def boletin_consolidado_gestion(self, usuario, gestion=None):
        """Devuelve una lista consolidada de todos los estudiantes con sus promedios por periodo para una gestion.
        Solo accesible para directores y secretarias."""
        if not self.ac.puede_ver_todo(usuario):
            raise PermissionError('No autorizado')

        if not gestion:
            from ..models import Periodos
            ultimo_periodo = Periodos.objects.filter(estado='activo').order_by('-gestion').first()
            if not ultimo_periodo:
                raise ValueError('No hay periodos activos')
            gestion = ultimo_periodo.gestion

        from ..models import Cursos, Inscripciones, Periodos
        cursos = Cursos.objects.filter(gestion=gestion, activo=True).select_related('grado', 'paralelo').order_by('grado__numero', 'paralelo__nombre')

        periodos = Periodos.objects.filter(gestion=gestion).order_by('fecha_inicio')

        resultado = []
        for curso in cursos:
            inscripciones = Inscripciones.objects.filter(
                curso=curso, gestion=gestion, estado='activo'
            ).select_related('estudiante')

            estudiantes_data = []
            for ins in inscripciones:
                try:
                    boletin = self.generar_boletin(usuario, ins.estudiante_id, gestion=gestion)
                    promedios_por_periodo = {}
                    for p in periodos:
                        notas_periodo = [
                            m['notas_por_periodo'].get(str(p.id)) or 0
                            for m in boletin['materias']
                        ]
                        promedios_por_periodo[str(p.id)] = round(sum(notas_periodo) / len(notas_periodo), 2) if notas_periodo else None

                    valores = list(promedios_por_periodo.values())
                    promedio_general = round(sum(valores) / len(valores), 2) if periodos else None

                    estudiantes_data.append({
                        'estudiante_id': ins.estudiante_id,
                        'rude': ins.estudiante.rude,
                        'nombres': ins.estudiante.nombres,
                        'primer_apellido': ins.estudiante.primer_apellido,
                        'segundo_apellido': ins.estudiante.segundo_apellido or '',
                        'promedios_por_periodo': promedios_por_periodo,
                        'promedio_general': promedio_general,
                    })
                except Exception:
                    continue

            if estudiantes_data:
                resultado.append({
                    'curso_id': curso.id,
                    'curso': str(curso),
                    'grado': curso.grado.nombre,
                    'paralelo': curso.paralelo.nombre,
                    'estudiantes': estudiantes_data,
                })

        return {
            'gestion': gestion,
            'periodos': [{'id': p.id, 'nombre': p.nombre} for p in periodos],
            'cursos': resultado,
        }
