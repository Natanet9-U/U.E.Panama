from collections import Counter
from io import BytesIO
from datetime import date
from pathlib import Path
import re

from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_PARAGRAPH_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from ..models import Asistencias, DocenteAsignacion, Estudiantes, Notas, Periodos
from .access_service import AccessControlService


class ReportsService:
    def __init__(self):
        self.access_service = AccessControlService()

    def build_reports_page(self, usuario, *, periodo_id=None):
        notes_queryset = Notas.objects.select_related(
            "estudiante__usuario",
            "asignacion__area",
            "asignacion__grado",
            "asignacion__docente__usuario",
            "periodo",
        ).order_by("-updated_at", "-created_at")
        notes_queryset = self.access_service.filter_notes_queryset(notes_queryset, usuario)
        if periodo_id:
            notes_queryset = notes_queryset.filter(periodo_id=periodo_id)
        notes = list(notes_queryset.filter(total__isnull=False))

        attendance_queryset = Asistencias.objects.select_related("estudiante__usuario", "estudiante__grado")
        attendance_queryset = self.access_service.filter_students_queryset(attendance_queryset, usuario)
        attendance = list(attendance_queryset)

        students_queryset = Estudiantes.objects.select_related("usuario", "grado")
        students_queryset = self.access_service.filter_students_queryset(students_queryset, usuario)

        summary = self._build_summary(notes, attendance, students_queryset.count())
        academic_report = self._build_academic_report(notes)
        attendance_report = self._build_attendance_report(attendance)
        risk_report = self._build_risk_report(notes)

        return {
            "resumen": summary,
            "reportes": [academic_report, attendance_report, risk_report],
            "top_estudiantes": self._build_top_students(notes),
            "alertas": self._build_alerts(notes, usuario),
            "cursos": self._build_courses(notes, usuario),
            "filtros": {
                "periodos": self._build_periods(),
            },
            "permisos": self.access_service.build_permissions_payload(usuario),
        }

    def build_report_document(self, usuario, *, periodo_id=None, trimestre=None):
        payload = self.build_reports_page(usuario, periodo_id=periodo_id)
        trimester_info = self._resolve_trimester_info(periodo_id=periodo_id, trimestre=trimestre)

        notes_queryset = Notas.objects.select_related(
            "estudiante__usuario",
            "estudiante__grado",
            "asignacion__area",
            "asignacion__grado",
            "periodo",
        )
        notes_queryset = self.access_service.filter_notes_queryset(notes_queryset, usuario)
        if periodo_id:
            notes_queryset = notes_queryset.filter(periodo_id=periodo_id)
        notes = list(notes_queryset.filter(total__isnull=False))

        students_queryset = Estudiantes.objects.select_related("usuario", "grado")
        students_queryset = self.access_service.filter_students_queryset(students_queryset, usuario)
        students = list(students_queryset)
        student_map = {student.id: student for student in students}

        document = Document()
        section = document.sections[0]
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

        normal_style = document.styles["Normal"]
        normal_style.font.name = "Times New Roman"
        normal_style.font.size = Pt(10.5)

        def add_paragraph(text, *, bold=False, italic=False, size=10.5, color=None, align=None, space_after=0):
            paragraph = document.add_paragraph()
            if align is not None:
                paragraph.alignment = align
            paragraph.paragraph_format.space_after = Pt(space_after)
            run = paragraph.add_run(text)
            run.bold = bold
            run.italic = italic
            run.font.name = "Times New Roman"
            run.font.size = Pt(size)
            if color is not None:
                run.font.color.rgb = color
            return paragraph

        def add_red_placeholder(paragraph, text):
            run = paragraph.add_run(text)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.color.rgb = RGBColor(192, 0, 0)
            return run

        def set_cell_shading(cell, fill):
            tc_pr = cell._tc.get_or_add_tcPr()
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), fill)
            tc_pr.append(shading)

        def set_cell_border(cell, *, color="FFFFFF", size="8"):
            tc_pr = cell._tc.get_or_add_tcPr()
            borders = tc_pr.find(qn("w:tcBorders"))
            if borders is None:
                borders = OxmlElement("w:tcBorders")
                tc_pr.append(borders)
            for edge in ("top", "left", "bottom", "right"):
                edge_el = borders.find(qn(f"w:{edge}"))
                if edge_el is None:
                    edge_el = OxmlElement(f"w:{edge}")
                    borders.append(edge_el)
                edge_el.set(qn("w:val"), "single")
                edge_el.set(qn("w:sz"), size)
                edge_el.set(qn("w:space"), "0")
                edge_el.set(qn("w:color"), color)

        def clear_cell(cell):
            cell.text = ""

        def write_cell_text(cell, text, *, bold=False, size=10, color=None, align=WD_ALIGN_PARAGRAPH.CENTER):
            clear_cell(cell)
            paragraph = cell.paragraphs[0]
            paragraph.alignment = align
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.space_before = Pt(0)
            run = paragraph.add_run(text)
            run.bold = bold
            run.font.name = "Times New Roman"
            run.font.size = Pt(size)
            if color is not None:
                run.font.color.rgb = color

        def write_cell_paragraphs(cell, paragraphs, *, align=WD_ALIGN_PARAGRAPH.LEFT, size=10):
            clear_cell(cell)
            for index, parts in enumerate(paragraphs):
                paragraph = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
                paragraph.alignment = align
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.space_before = Pt(0)
                for part in parts:
                    run = paragraph.add_run(part.get("text", ""))
                    run.bold = part.get("bold", False)
                    run.italic = part.get("italic", False)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(part.get("size", size))
                    run.font.color.rgb = part.get("color", RGBColor(255, 255, 255))

        def style_table(table, *, header_fill="6B4F00", body_fill="2B2B2B"):
            table.style = "Table Grid"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for row_index, row in enumerate(table.rows):
                for cell in row.cells:
                    set_cell_shading(cell, header_fill if row_index == 0 else body_fill)
                    set_cell_border(cell)
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.space_after = Pt(0)
                        paragraph.paragraph_format.space_before = Pt(0)
                        for run in paragraph.runs:
                            run.font.name = "Times New Roman"
                            run.font.size = Pt(10)
                            if run.font.color.rgb is None:
                                run.font.color.rgb = RGBColor(255, 255, 255)
                            if row_index == 0:
                                run.bold = True

        def add_heading_line(text):
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(2)
            run = paragraph.add_run(text)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(14)
            return paragraph

        def add_section_heading(number, title):
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.space_before = Pt(8)
            paragraph.paragraph_format.space_after = Pt(4)
            run = paragraph.add_run(f"{number}.	{title}")
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            return paragraph

        def add_section_table(headers, rows):
            table = document.add_table(rows=1, cols=len(headers))
            for index, header in enumerate(headers):
                write_cell_text(table.rows[0].cells[index], header, bold=True, size=9)
            for row_values in rows:
                cells = table.add_row().cells
                for index, value in enumerate(row_values):
                    if isinstance(value, str) and value.startswith("(") and value.endswith(")"):
                        write_cell_text(cells[index], value, size=9, color=RGBColor(192, 0, 0))
                    else:
                        write_cell_text(cells[index], str(value), size=9)
            style_table(table)
            return table

        header_logo = self._report_asset_path("logo-Colegio.png")
        if header_logo is not None:
            header_paragraph = section.header.paragraphs[0]
            header_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            header_paragraph.paragraph_format.space_after = Pt(0)
            header_paragraph.add_run().add_picture(str(header_logo), width=Inches(0.95))

        header_title = section.header.add_paragraph()
        header_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_title.paragraph_format.space_after = Pt(0)
        title_run = header_title.add_run("DIRECCION DISTRITAL DE EDUCACION LA PAZ – 2\nUNIDAD EDUCATIVA REPÚBLICA DE PANAMÁ")
        title_run.bold = True
        title_run.font.name = "Times New Roman"
        title_run.font.size = Pt(13)
        title_run.font.color.rgb = RGBColor(141, 169, 197)

        header_subtitle = section.header.add_paragraph()
        header_subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_subtitle.paragraph_format.space_after = Pt(0)
        subtitle_run = header_subtitle.add_run(f"{trimester_info['label']}\nPRIMARIA COMUNITARIA VOCACIONAL")
        subtitle_run.bold = True
        subtitle_run.font.name = "Times New Roman"
        subtitle_run.font.size = Pt(11)
        subtitle_run.font.color.rgb = RGBColor(221, 102, 102)

        header_code = section.header.add_paragraph()
        header_code.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_code.paragraph_format.space_after = Pt(0)
        code_run = header_code.add_run("CODIGO SIE: (CODIGO SIE)")
        code_run.bold = True
        code_run.font.name = "Times New Roman"
        code_run.font.size = Pt(10)
        code_run.font.color.rgb = RGBColor(141, 169, 197)

        add_heading_line(trimester_info["report_title"])

        meta = document.add_table(rows=5, cols=2)
        meta_rows = [
            ("A:", "(NOMBRE DE LA DIRECTORA)"),
            ("DE:", "(NOMBRE DEL DOCENTE)"),
            ("CURSO:", "(CURSO)"),
            ("REF.", trimester_info["reference"]),
            ("FECHA:", "(LUGAR, FECHA)"),
        ]
        for index, (label, value) in enumerate(meta_rows):
            write_cell_text(meta.rows[index].cells[0], label, bold=True, size=10, align=WD_ALIGN_PARAGRAPH.LEFT)
            paragraph = meta.rows[index].cells[1].paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.space_before = Pt(0)
            if value.startswith("("):
                add_red_placeholder(paragraph, value)
            else:
                run = paragraph.add_run(value)
                run.font.name = "Times New Roman"
                run.font.size = Pt(10)
        style_table(meta, header_fill="3F3F3F", body_fill="1F1F1F")

        document.add_paragraph("")
        add_paragraph("Señora Directora:", bold=True)
        add_paragraph(
            f"Dando cumplimiento al calendario institucional 2025 e Instructivo 12/25 emanado por su autoridad presento el siguiente informe correspondiente al {trimester_info['label'].title()}.",
            size=10.5,
        )
        add_paragraph(
            f"Por intermedio de la presente me dirijo a su autoridad, para hacer de su conocimiento sobre la etapa del {trimester_info['label'].lower()} de la gestión {trimester_info['year']} en el {payload['reportes'][0]['periodo'] if payload.get('reportes') else '(CURSO)' }.",
            size=10.5,
        )
        add_paragraph("(PRESENTACION DEL PROFESOR: DESARROLLE AQUÍ EL TEXTO QUE DEBE IR EN ESTE APARTADO)", color=RGBColor(192, 0, 0), size=10.5)

        student_totals = {}
        for note in notes:
            student_totals.setdefault(note.estudiante_id, []).append(note.total)

        def gender_bucket(value):
            normalized = (value or "").strip().upper()
            if normalized in {"M", "V", "1", "H"}:
                return "V"
            if normalized in {"F", "2"}:
                return "M"
            return None

        visible_student_ids = {student.id for student in students}
        effective_student_ids = set(student_totals.keys())
        approved_ids = set()
        failed_ids = set()
        for student_id, totals in student_totals.items():
            average = sum(totals) / len(totals)
            if average >= 70:
                approved_ids.add(student_id)
            else:
                failed_ids.add(student_id)

        section_1_counts = {
            "INSCRITOS": {"V": 0, "M": 0, "T": len(visible_student_ids), "%": 100 if visible_student_ids else 0},
            "NO INCORPORADOS": {"V": 0, "M": 0, "T": max(len(visible_student_ids) - len(effective_student_ids), 0), "%": round(((len(visible_student_ids) - len(effective_student_ids)) / len(visible_student_ids)) * 100) if visible_student_ids else 0},
            "EFECTIVOS": {"V": 0, "M": 0, "T": len(effective_student_ids), "%": round((len(effective_student_ids) / len(visible_student_ids)) * 100) if visible_student_ids else 0},
            "APROBADOS": {"V": 0, "M": 0, "T": len(approved_ids), "%": round((len(approved_ids) / len(effective_student_ids)) * 100) if effective_student_ids else 0},
            "REPROBADOS": {"V": 0, "M": 0, "T": len(failed_ids), "%": round((len(failed_ids) / len(effective_student_ids)) * 100) if effective_student_ids else 0},
        }

        student_by_id = {student.id: student for student in students}
        for student_id in approved_ids | failed_ids:
            student = student_by_id.get(student_id)
            if student is None:
                continue
            bucket = gender_bucket(getattr(student, "genero", None))
            if bucket is None:
                continue
            target = "APROBADOS" if student_id in approved_ids else "REPROBADOS"
            section_1_counts[target][bucket] += 1

        add_section_heading(1, "ESTADÍSTICA DE ESTUDIANTES")
        section_1 = document.add_table(rows=2, cols=20)
        section_1_headers = ["INSCRITOS", "", "", "", "NO INCORPORADOS", "", "", "", "EFECTIVOS", "", "", "", "APROBADOS", "", "", "", "REPROBADOS", "", "", ""]
        for index, header in enumerate(section_1_headers):
            write_cell_text(section_1.rows[0].cells[index], header, bold=True, size=9)
        group_order = ["INSCRITOS", "NO INCORPORADOS", "EFECTIVOS", "APROBADOS", "REPROBADOS"]
        for group_index, group_name in enumerate(group_order):
            base = group_index * 4
            values = section_1_counts[group_name]
            for offset, key in enumerate(["V", "M", "T", "%"]):
                write_cell_text(section_1.rows[1].cells[base + offset], str(values[key]), size=9)
        style_table(section_1)

        add_section_heading(2, "ESTADISTICA DE TEMAS PROGRAMADOS Y AVANZADOS")
        section_2_headers = ["ÁREA O ASIGNATURA", "TEMAS PLANIFICADOS", "TEMAS AVANZADOS", "%", "TEMAS PENDIENTES", "%", "OBS."]
        section_2_rows = []
        for subject in (payload.get("reportes", [{}])[0].get("labels") or ["Comunicación y lenguajes", "Ciencias Sociales", "Artes Plásticas y visuales", "Matemática", "Ciencias Naturales"]):
            section_2_rows.append([subject, "( )", "( )", "( )", "( )", "( )", "( )"])
        add_section_table(section_2_headers, section_2_rows)

        add_section_heading(3, "ESTADÍSTICA DE PROMEDIOS DE REPROBACIÓN.")
        section_3 = document.add_table(rows=6, cols=13)
        section_3_headers = ["ÁREA", "1ER TRIMESTRE", "", "", "2DO TRIMESTRE", "", "", "3ER TRIMESTRE", "", "", "TOTAL", "", ""]
        for index, header in enumerate(section_3_headers):
            write_cell_text(section_3.rows[0].cells[index], header, bold=True, size=9)

        trimester_map = {1: 1, 2: 4, 3: 7}
        area_order = ["COMUNICACIÓN Y LENGUAJE", "CIENCIAS SOCIALES", "ARTES PLÁSTICAS Y VISUALES.", "MATEMATICA", "CIENCIAS NATURALES"]
        failed_by_area = {}
        for note in notes:
            if note.total >= 70:
                continue
            area_name = (getattr(note.asignacion.area, "nombre", "") or "").strip().upper()
            trimester_number = getattr(note.periodo, "numero", None)
            student = student_by_id.get(note.estudiante_id)
            bucket = gender_bucket(getattr(student, "genero", None)) if student else None
            failed_by_area.setdefault(area_name, {1: {"V": 0, "M": 0, "T": 0}, 2: {"V": 0, "M": 0, "T": 0}, 3: {"V": 0, "M": 0, "T": 0}, "TOTAL": {"V": 0, "M": 0, "T": 0}})
            if trimester_number in trimester_map and bucket:
                failed_by_area[area_name][trimester_number][bucket] += 1
                failed_by_area[area_name][trimester_number]["T"] += 1
            if bucket:
                failed_by_area[area_name]["TOTAL"][bucket] += 1
                failed_by_area[area_name]["TOTAL"]["T"] += 1

        for row_index, area_name in enumerate(area_order, start=1):
            row = section_3.rows[row_index].cells
            write_cell_text(row[0], area_name, bold=True, size=9, align=WD_ALIGN_PARAGRAPH.LEFT)
            area_values = failed_by_area.get(area_name, {})
            for trimester_number, start_index in trimester_map.items():
                trimester_values = area_values.get(trimester_number, {"V": 0, "M": 0, "T": 0})
                for offset, key in enumerate(["V", "M", "T"]):
                    write_cell_text(row[start_index + offset], str(trimester_values[key]), size=9)
            total_values = area_values.get("TOTAL", {"V": 0, "M": 0, "T": 0})
            for offset, key in enumerate(["V", "M", "T"]):
                write_cell_text(row[10 + offset], str(total_values[key]), size=9)
        style_table(section_3)

        add_section_heading(4, "ASPECTO PEDAGÓGICO")
        add_section_table(
            ["AREA", "LOGROS ALCANZADOS", "DIFICULTADES", "SUGERENCIAS PARA MEJORAR"],
            [
                ["COMUNICACIÓN Y LENGUAJE", "(LOGROS ALCANZADOS)", "(DIFICULTADES)", "(SUGERENCIAS)"],
                ["CIENCIAS SOCIALES", "(LOGROS ALCANZADOS)", "(DIFICULTADES)", "(SUGERENCIAS)"],
                ["ARTES PLASTICAS", "(LOGROS ALCANZADOS)", "(DIFICULTADES)", "(SUGERENCIAS)"],
                ["CIENCIAS NATURALES", "(LOGROS ALCANZADOS)", "(DIFICULTADES)", "(SUGERENCIAS)"],
                ["MATEMATICA", "(LOGROS ALCANZADOS)", "(DIFICULTADES)", "(SUGERENCIAS)"],
            ],
        )

        add_section_heading(5, "ATENCIÓN ESCOLAR A ESTUDIANTES CON DISCAPACIDAD Y/O CONDICION  (intelectual leve, autismo, TDH, TDA)")
        add_section_table(
            ["NOMBRE DEL ESTUDIANTE", "INFORME PROFESIONAL EXTERNO", "ADAPTACIONES CURRICULARES  Y LOGROS ALCANZADOS", "DIFICULTADES"],
            [["(NOMBRE DEL ESTUDIANTE)", "(INFORME PROFESIONAL EXTERNO)", "(ADAPTACIONES CURRICULARES Y LOGROS ALCANZADOS)", "(DIFICULTADES)"]],
        )
        add_paragraph("RECOMENDACIÓN/SUGERENCIAS:", bold=True, size=10.5)

        add_section_heading(6, "ESTUDIANTES CON REPROVACIÓN ANUAL")
        failing_students = []
        for student_id in sorted(failed_ids, key=lambda item: str(item)):
            student = student_by_id.get(student_id)
            if student is None:
                continue
            average = round(sum(student_totals.get(student_id, [])) / len(student_totals.get(student_id, [])), 1)
            failing_students.append([f"{student.nombres} {student.primer_apellido}".strip(), "(AREA)", str(average), "(CAUSAS)", "(ACCIONES REALIZADAS)"])
        if not failing_students:
            failing_students = [["(NOMBRE DEL ESTUDIANTE)", "(AREA)", "(PROMEDIO)", "(CAUSAS)", "(ACCIONES REALIZADAS)"]]
        add_section_table(
            ["NOMBRE DEL ESTUDIANTE", "AREA", "PROMEDIO", "CAUSAS", "ACCIONES REALIZADAS"],
            failing_students,
        )

        add_section_heading(7, "LECTURA (10 MINUTOS)")
        section_7 = document.add_table(rows=2, cols=3)
        for index, header in enumerate(["TIPO DE LECTURA", "ESTRATEGIA METODOLOGICA", "OBSERVACION"]):
            write_cell_text(section_7.rows[0].cells[index], header, bold=True, size=9)
        write_cell_text(section_7.rows[1].cells[0], "Cuentos para cada día.\nFábulas de Esopo.", align=WD_ALIGN_PARAGRAPH.LEFT, size=10)
        write_cell_paragraphs(
            section_7.rows[1].cells[1],
            [
                [
                    {"text": "Práctica: ", "bold": True},
                    {"text": "Se lee en voz alta un cuento, se ayuda a comprenderlo, la identificación de las partes del cuento, con preguntas."},
                ],
                [
                    {"text": "Teoría: ", "bold": True},
                    {"text": "identificamos las partes del cuento, durante la lectura"},
                ],
                [
                    {"text": "Valoración: ", "bold": True},
                    {"text": "reflexionamos acerca del cuento o fabula, si hay una enseñanza."},
                ],
                [
                    {"text": "Producción: ", "bold": True},
                    {"text": "en su cuaderno dibujan las 3 partes del cuento y escriben una oración corta."},
                ],
            ],
            align=WD_ALIGN_PARAGRAPH.LEFT,
            size=10,
        )
        write_cell_text(section_7.rows[1].cells[2], "", align=WD_ALIGN_PARAGRAPH.LEFT, size=10)
        style_table(section_7)

        add_section_heading(8, "CONCRECION DEL PROYECTO SOCIOPRODUCTIVO")
        add_section_table(
            ["ACTIVIDAD", "LOGROS ALCANZADOS", "DIFICULTADES", "SUGERENCIA"],
            [["(ACTIVIDAD)", "(LOGROS ALCANZADOS)", "(DIFICULTADES)", "(SUGERENCIA)"]],
        )

        document.add_paragraph("Es cuanto puedo informar en honor a la verdad.")
        closing = document.add_paragraph()
        closing.alignment = WD_ALIGN_PARAGRAPH.CENTER
        closing.add_run("Atentamente.")
        document.add_paragraph("")
        document.add_paragraph("Firma y sello lineal maestro")

        document.add_paragraph("")
        document.add_paragraph(f"ESTUDIANTES DESTACADOS DURANTE LA GESTION {trimester_info['year']} 2do “A” de primaria")
        for student in payload.get("top_estudiantes", []):
            bullet = document.add_paragraph(style="List Bullet")
            bullet.add_run(student["nombre"])

        document.add_paragraph("Profesora: (NOMBRE DE LA DOCENTE)")
        footer_logo = self._report_asset_path("logo-Colegio.png")
        footer_table = section.footer.add_table(rows=1, cols=2, width=Inches(6.9))
        footer_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        footer_table.autofit = True
        footer_logo_cell = footer_table.rows[0].cells[0]
        footer_logo_cell.width = Inches(1.5)
        footer_logo_paragraph = footer_logo_cell.paragraphs[0]
        footer_logo_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        footer_logo_paragraph.paragraph_format.space_after = Pt(0)
        if footer_logo is not None:
            footer_logo_paragraph.add_run().add_picture(str(footer_logo), width=Inches(0.85))
        footer_text_cell = footer_table.rows[0].cells[1]
        footer_text_paragraph = footer_text_cell.paragraphs[0]
        footer_text_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_text_paragraph.paragraph_format.space_after = Pt(0)
        footer_text_run = footer_text_paragraph.add_run(f"{trimester_info['year']} de Bolivia")
        footer_text_run.bold = True
        footer_text_run.font.name = "Times New Roman"
        footer_text_run.font.size = Pt(11)
        document.add_paragraph(f"Generado por el sistema el {date.today().strftime('%d/%m/%Y')}")

        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()

    def _report_asset_path(self, filename):
        base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parents[2]))
        candidate = base_dir.parent / "frontend" / "public" / "assets" / "login" / filename
        return candidate if candidate.exists() else None

    def _resolve_trimester_info(self, *, periodo_id=None, trimestre=None):
        trimester_number = self._parse_trimester_value(trimestre)
        periodo = None
        if periodo_id:
            periodo = Periodos.objects.filter(id=periodo_id).first()
            if trimester_number is None and periodo is not None:
                trimester_number = self._parse_trimester_value(getattr(periodo, "numero", None))
                if trimester_number is None:
                    trimester_number = self._parse_trimester_value(getattr(periodo, "nombre", None))

        if trimester_number not in {1, 2, 3}:
            trimester_number = 3

        trimester_labels = {1: "PRIMER", 2: "SEGUNDO", 3: "TERCER"}
        year = getattr(periodo, "gestion", None) or timezone.localdate().year
        return {
            "numero": trimester_number,
            "label": f"{trimester_labels[trimester_number]} TRIMESTRE",
            "report_title": f"INFORME {trimester_labels[trimester_number]} TRIMESTRE",
            "reference": f"INFORME TÉCNICO PEDAGÓGICO {trimester_labels[trimester_number]} TRIMESTRE",
            "year": year,
        }

    def _parse_trimester_value(self, value):
        if value is None:
            return None

        text = str(value).strip().lower()
        if not text:
            return None

        explicit = {
            "1": 1,
            "1er": 1,
            "primer": 1,
            "primero": 1,
            "2": 2,
            "2do": 2,
            "segundo": 2,
            "3": 3,
            "3er": 3,
            "tercer": 3,
        }
        if text in explicit:
            return explicit[text]

        match = re.search(r"\b([123])\b", text)
        if match:
            return int(match.group(1))

        return None

    def _build_summary(self, notes, attendance, visible_students):
        graded_count = len(notes)
        average = sum(note.total for note in notes) / graded_count if graded_count else 0
        attendance_rate = self._attendance_rate(attendance)
        featured = sum(1 for note in notes if note.total >= 90)
        courses = self._visible_courses_count(notes)
        return [
            {"titulo": "Promedio General", "valor": f"{average:.1f}", "detalle": "Promedio de notas visibles", "acento": "blue"},
            {"titulo": "Asistencia", "valor": f"{attendance_rate}%", "detalle": "Asistencia acumulada", "acento": "green"},
            {"titulo": "Destacados", "valor": str(featured), "detalle": "Notas sobre 90", "acento": "violet"},
            {"titulo": "Cursos Visibles", "valor": str(courses), "detalle": f"{visible_students} estudiantes en alcance", "acento": "orange"},
        ]

    def _build_academic_report(self, notes):
        period_name = self._current_period_name(notes)
        averages = self._subject_averages(notes)
        return {
            "titulo": "Rendimiento Académico",
            "estado": "Generado",
            "periodo": period_name,
            "detalle": "Consolidado de rendimiento por asignatura",
            "labels": [item[0] for item in averages],
            "data": [item[1] for item in averages],
        }

    def _build_attendance_report(self, attendance):
        per_grade = Counter()
        for record in attendance:
            grade_label = f"{record.estudiante.grado.nivel} {record.estudiante.grado.numero}{record.estudiante.grado.paralelo}"
            per_grade[grade_label] += 1

        labels = list(per_grade.keys())
        data = list(per_grade.values())
        return {
            "titulo": "Asistencia por Grado",
            "estado": "Generado",
            "periodo": timezone.localdate().strftime("%B %Y"),
            "detalle": "Registro de asistencias acumuladas por curso",
            "labels": labels,
            "data": data,
        }

    def _build_risk_report(self, notes):
        low_performance = [note for note in notes if note.total < 70]
        return {
            "titulo": "Estudiantes en Riesgo",
            "estado": "Generado" if low_performance else "Sin incidencias",
            "periodo": self._current_period_name(notes),
            "detalle": "Estudiantes con promedio bajo requerirán seguimiento",
            "cantidad": len(low_performance),
            "porcentaje": self._percentage(len(low_performance), len(notes)),
        }

    def _build_top_students(self, notes):
        ranking = {}
        for note in notes:
            ranking.setdefault(note.estudiante_id, []).append(note.total)

        items = []
        for student_id, values in ranking.items():
            student = next((note.estudiante for note in notes if note.estudiante_id == student_id), None)
            if student is None:
                continue

            promedio = round(sum(values) / len(values), 1)
            items.append(
                {
                    "nombre": f"{student.nombres} {student.primer_apellido}".strip(),
                    "promedio": promedio,
                    "mensaje": "Excelente rendimiento" if promedio >= 90 else "Buen desempeño",
                }
            )

        return sorted(items, key=lambda item: item["promedio"], reverse=True)[:5]

    def _build_alerts(self, notes, usuario):
        alerts = []
        low_notes = [note for note in notes if note.total < 70]
        if low_notes:
            alerts.append(
                {
                    "titulo": "Seguimiento académico",
                    "detalle": f"Hay {len(low_notes)} calificaciones por debajo de 70 en el alcance visible.",
                    "tipo": "warning",
                }
            )

        pending_notes = Notas.objects.filter(total__isnull=True)
        pending_notes = self.access_service.filter_notes_queryset(pending_notes, usuario)
        if pending_notes.exists():
            alerts.append(
                {
                    "titulo": "Calificaciones pendientes",
                    "detalle": f"Existen {pending_notes.count()} calificaciones sin registrar.",
                    "tipo": "info",
                }
            )

        if not alerts:
            alerts.append({"titulo": "Sin alertas", "detalle": "No se detectaron incidencias en el alcance actual.", "tipo": "success"})

        return alerts

    def _build_courses(self, notes, usuario):
        assignment_ids = self.access_service.get_assigned_assignment_ids(usuario)
        queryset = DocenteAsignacion.objects.select_related("area", "grado", "docente__usuario")
        if not self.access_service.can_view_all_academic_data(usuario):
            queryset = queryset.filter(id__in=assignment_ids)

        courses = []
        for assignment in queryset:
            assignment_notes = [note for note in notes if note.asignacion_id == assignment.id]
            if not assignment_notes:
                continue

            average = round(sum(note.total for note in assignment_notes) / len(assignment_notes), 1)
            courses.append(
                {
                    "nombre": assignment.area.nombre,
                    "grado": f"{assignment.grado.nivel} {assignment.grado.numero}{assignment.grado.paralelo}",
                    "promedio": average,
                    "estudiantes": len({note.estudiante_id for note in assignment_notes}),
                }
            )

        return sorted(courses, key=lambda item: item["promedio"], reverse=True)[:6]

    def _subject_averages(self, notes):
        grouped = {}
        for note in notes:
            subject = note.asignacion.area.nombre
            grouped.setdefault(subject, []).append(note.total)

        return [(subject, round(sum(values) / len(values), 1)) for subject, values in grouped.items()]

    def _attendance_rate(self, attendance):
        if not attendance:
            return 0

        present = sum(1 for record in attendance if self._is_positive_state(record.estado))
        return round((present / len(attendance)) * 100)

    def _visible_courses_count(self, notes):
        return len({note.asignacion_id for note in notes})

    def _current_period_name(self, notes):
        if not notes:
            return "Sin periodo visible"

        period = notes[0].periodo
        return f"{period.nombre} {period.gestion}"

    def _build_periods(self):
        periods = Periodos.objects.order_by("-gestion", "-numero")
        return [{"id": str(period.id), "nombre": f"{period.nombre} {period.gestion}"} for period in periods]

    def _percentage(self, numerator, denominator):
        if not denominator:
            return 0
        return round((numerator / denominator) * 100)

    def _is_positive_state(self, estado):
        estado_normalizado = (estado or "").strip().lower()
        return estado_normalizado not in {"falta", "ausente", "inasistencia"}