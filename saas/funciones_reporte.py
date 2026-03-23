import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from datetime import date, datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import os

PAGE_W, PAGE_H = A4


# =========================================================
# UTILIDADES VECTORIALES
# =========================================================
def _rect(c, x, y, w, h, lw=0.6):
    c.setLineWidth(lw)
    c.rect(x, y, w, h, stroke=1, fill=0)

def _line(c, x1, y1, x2, y2, lw=0.6):
    c.setLineWidth(lw)
    c.line(x1, y1, x2, y2)

def _txt(c, x, y, text, size=8, bold=False):
    if text is None:
        text = ""
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, str(text))

def _wrap_lines(text, font="Helvetica", size=8, max_w=200):
    if not text:
        return [""]
    words = str(text).split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if stringWidth(test, font, size) <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines or [""]

def _txt_wrap(c, x, y, text, w, size=8, leading=10, bold=False, max_lines=None):
    font = "Helvetica-Bold" if bold else "Helvetica"
    lines = _wrap_lines(text, font=font, size=size, max_w=w)
    if max_lines:
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        _txt(c, x, y - i * leading, ln, size=size, bold=bold)

def _checkbox(c, x, y, size=9, checked=False):
    _rect(c, x, y, size, size, lw=0.6)
    if checked:
        _txt(c, x + 2, y + 1, "X", size=9, bold=True)

def _title_bar(c, x, y, w, h, title):
    c.setFillColor(colors.lightgrey)
    c.rect(x, y, w, h, stroke=1, fill=1)
    c.setFillColor(colors.black)
    _txt(c, x + 6, y + h - 12, title, size=9, bold=True)

def _fmt_date(d):
    if not d:
        return ""
    if isinstance(d, str):
        return d
    try:
        return d.strftime("%Y-%m-%d")
    except Exception:
        return str(d)

def _fmt_bool_x(v):
    return "X" if bool(v) else ""

def _safe(getter, default=""):
    try:
        v = getter()
        return default if v is None else v
    except Exception:
        return default


# =========================================================
# LAYOUT ANEXO 1 (ajustable 1 sola vez)
# =========================================================
LAYOUT_A1 = {
    "margin": 26,

    # Header
    "header_h": 56,

    # Secciones (alturas estimadas)
    "sec1_h": 86,   # datos del establecimiento
    "sec2_h": 110,  # datos trabajador
    "sec3_h": 92,   # fechas + tipo evaluación + motivo
    "sec4_h": 120,  # antecedentes
    "sec5_h": 70,   # hábitos
    "sec6_h": 78,   # signos vitales
    "sec7_h": 210,  # examen físico (mucho texto)
    "sec8_h": 96,   # aptitud/retiro + recomendación
}


def draw_anexo1(c, ev=None):
    """
    ANEXO 1 vectorial (sin imágenes).
    Dibuja TODA la estructura principal y, si ev existe, imprime datos.
    """
    M = LAYOUT_A1["margin"]
    X = M
    W = PAGE_W - 2 * M
    y = PAGE_H - M  # cursor superior

    # =========================
    # HEADER
    # =========================
    y -= LAYOUT_A1["header_h"]
    _rect(c, X, y, W, LAYOUT_A1["header_h"])
    _txt(c, X + 10, y + 38, "EVALUACIÓN MÉDICA OCUPACIONAL (FEMO)", 12, True)
    _txt(c, X + 10, y + 22, "FORMULARIO - ANEXO 1 (ANVERSO)", 9, True)

    # =========================
    # 1) DATOS DEL ESTABLECIMIENTO
    # =========================
    y -= 8
    y -= LAYOUT_A1["sec1_h"]
    _title_bar(c, X, y + LAYOUT_A1["sec1_h"] - 18, W, 18, "1. DATOS DEL ESTABLECIMIENTO / INSTITUCIÓN")
    _rect(c, X, y, W, LAYOUT_A1["sec1_h"] - 18)

    # Grid
    top = y + (LAYOUT_A1["sec1_h"] - 18)
    row_h = (LAYOUT_A1["sec1_h"] - 18) / 3
    _line(c, X, top - row_h, X + W, top - row_h)
    _line(c, X, top - 2 * row_h, X + W, top - 2 * row_h)

    split = X + W * 0.62
    _line(c, split, y, split, top)

    # Labels
    _txt(c, X + 6, top - 12, "Institución del sistema:", 8, True)
    _txt(c, X + 6, top - row_h - 12, "RUC:", 8, True)
    _txt(c, X + 160, top - row_h - 12, "CIU:", 8, True)

    _txt(c, split + 6, top - 12, "Establecimiento de trabajo:", 8, True)
    _txt(c, split + 6, top - row_h - 12, "No. Historia clínica:", 8, True)
    _txt(c, split + 160, top - row_h - 12, "No. Archivo:", 8, True)

    # Values
    if ev:
        _txt_wrap(c, X + 150, top - 12, _safe(lambda: ev.institucion_sistema), w=split - (X + 160), size=8, leading=9, max_lines=1)
        _txt(c, X + 40, top - row_h - 12, _safe(lambda: ev.ruc), 8)
        _txt(c, X + 190, top - row_h - 12, _safe(lambda: ev.ciu), 8)

        _txt_wrap(c, split + 170, top - 12, _safe(lambda: ev.establecimiento_trabajo), w=(X + W) - (split + 176), size=8, leading=9, max_lines=1)
        _txt(c, split + 120, top - row_h - 12, _safe(lambda: ev.numero_historia_clinica), 8)
        _txt(c, split + 220, top - row_h - 12, _safe(lambda: ev.numero_archivo), 8)

    # =========================
    # 2) DATOS DEL TRABAJADOR
    # =========================
    y -= 10
    y -= LAYOUT_A1["sec2_h"]
    _title_bar(c, X, y + LAYOUT_A1["sec2_h"] - 18, W, 18, "2. DATOS DEL TRABAJADOR")
    _rect(c, X, y, W, LAYOUT_A1["sec2_h"] - 18)

    top = y + (LAYOUT_A1["sec2_h"] - 18)
    # 3 filas
    row_h = (LAYOUT_A1["sec2_h"] - 18) / 3
    _line(c, X, top - row_h, X + W, top - row_h)
    _line(c, X, top - 2 * row_h, X + W, top - 2 * row_h)
    # 4 columnas
    c1 = X + W * 0.25
    c2 = X + W * 0.50
    c3 = X + W * 0.75
    for cx in (c1, c2, c3):
        _line(c, cx, y, cx, top)

    _txt(c, X + 6, top - 12, "Apellidos:", 8, True)
    _txt(c, c1 + 6, top - 12, "Nombres:", 8, True)
    _txt(c, c2 + 6, top - 12, "Identificación:", 8, True)
    _txt(c, c3 + 6, top - 12, "Puesto/CIU:", 8, True)

    _txt(c, X + 6, top - row_h - 12, "Grupo atención prioritaria:", 8, True)
    _txt(c, c1 + 6, top - row_h - 12, "Sexo:", 8, True)
    _txt(c, c2 + 6, top - row_h - 12, "Fecha nacimiento:", 8, True)
    _txt(c, c3 + 6, top - row_h - 12, "Edad:", 8, True)

    _txt(c, X + 6, top - 2 * row_h - 12, "Grupo sanguíneo:", 8, True)
    _txt(c, c1 + 6, top - 2 * row_h - 12, "Lateralidad:", 8, True)
    _txt(c, c2 + 6, top - 2 * row_h - 12, "Teléfono:", 8, True)
    _txt(c, c3 + 6, top - 2 * row_h - 12, "Correo:", 8, True)

    if ev:
        # Trabajador/persona (ajusta a tus campos reales)
        ap1 = _safe(lambda: ev.persona.primerapellido)
        ap2 = _safe(lambda: ev.persona.segundoapellido)
        nom = _safe(lambda: ev.persona.nombres)
        ident = _safe(lambda: ev.persona.identificacion)

        _txt_wrap(c, X + 75, top - 12, f"{ap1} {ap2}".strip(), w=c1 - (X + 80), size=8, max_lines=1)
        _txt_wrap(c, c1 + 75, top - 12, nom, w=c2 - (c1 + 80), size=8, max_lines=1)
        _txt(c, c2 + 90, top - 12, ident, 8)
        _txt_wrap(c, c3 + 80, top - 12, _safe(lambda: ev.puesto_trabajo_ciu), w=(X + W) - (c3 + 86), size=8, max_lines=1)

        _txt_wrap(c, X + 175, top - row_h - 12, _safe(lambda: ev.grupo_atencion_prioritaria), w=c1 - (X + 180), size=8, max_lines=1)

        sexo = _safe(lambda: ev.sexo, "")
        _checkbox(c, c1 + 60, top - row_h - 18, checked=(sexo == "M"))
        _txt(c, c1 + 72, top - row_h - 12, "M", 8)
        _checkbox(c, c1 + 90, top - row_h - 18, checked=(sexo == "F"))
        _txt(c, c1 + 102, top - row_h - 12, "F", 8)

        fn = _safe(lambda: ev.fecha_nacimiento, None)
        _txt(c, c2 + 110, top - row_h - 12, _fmt_date(fn), 8)
        _txt(c, c3 + 40, top - row_h - 12, _safe(lambda: ev.edad), 8)

        _txt(c, X + 105, top - 2 * row_h - 12, _safe(lambda: ev.grupo_sanguineo), 8)
        _txt(c, c1 + 90, top - 2 * row_h - 12, _safe(lambda: ev.lateralidad), 8)
        _txt(c, c2 + 80, top - 2 * row_h - 12, _safe(lambda: ev.persona.telefono), 8)
        _txt(c, c3 + 65, top - 2 * row_h - 12, _safe(lambda: ev.persona.email), 8)

    # =========================
    # 3) FECHAS / TIPO EVALUACIÓN / MOTIVO
    # =========================
    y -= 10
    y -= LAYOUT_A1["sec3_h"]
    _title_bar(c, X, y + LAYOUT_A1["sec3_h"] - 18, W, 18, "3. DATOS DE ATENCIÓN / TIPO DE EVALUACIÓN")
    _rect(c, X, y, W, LAYOUT_A1["sec3_h"] - 18)

    top = y + (LAYOUT_A1["sec3_h"] - 18)
    row_h = (LAYOUT_A1["sec3_h"] - 18) / 3
    _line(c, X, top - row_h, X + W, top - row_h)
    _line(c, X, top - 2 * row_h, X + W, top - 2 * row_h)

    split = X + W * 0.50
    _line(c, split, y, split, top)

    _txt(c, X + 6, top - 12, "Fecha atención:", 8, True)
    _txt(c, X + 6, top - row_h - 12, "Fecha ingreso trabajo:", 8, True)
    _txt(c, X + 6, top - 2 * row_h - 12, "Motivo de consulta:", 8, True)

    _txt(c, split + 6, top - 12, "Tipo evaluación:", 8, True)
    _txt(c, split + 6, top - row_h - 12, "Reintegro:", 8, True)
    _txt(c, split + 6, top - 2 * row_h - 12, "Último día laboral:", 8, True)

    # checkboxes tipo
    ty_y = top - 24
    _txt(c, split + 105, ty_y + 10, "Ingreso", 7)
    _txt(c, split + 185, ty_y + 10, "Periódico", 7)
    _txt(c, split + 275, ty_y + 10, "Reintegro", 7)
    _txt(c, split + 360, ty_y + 10, "Retiro", 7)
    _checkbox(c, split + 90, ty_y, checked=(ev and ev.tipo_evaluacion == "INGRESO"))
    _checkbox(c, split + 170, ty_y, checked=(ev and ev.tipo_evaluacion == "PERIODICO"))
    _checkbox(c, split + 260, ty_y, checked=(ev and ev.tipo_evaluacion == "REINTEGRO"))
    _checkbox(c, split + 340, ty_y, checked=(ev and ev.tipo_evaluacion == "RETIRO"))

    if ev:
        _txt(c, X + 90, top - 12, _fmt_date(_safe(lambda: ev.fecha_atencion)), 8)
        _txt(c, X + 130, top - row_h - 12, _fmt_date(_safe(lambda: ev.fecha_ingreso_trabajo)), 8)
        _txt_wrap(c, X + 110, top - 2 * row_h - 12, _safe(lambda: ev.motivo_consulta), w=split - (X + 120), size=8, leading=9, max_lines=2)
        _txt(c, split + 90, top - row_h - 12, _fmt_date(_safe(lambda: ev.fecha_reintegro)), 8)
        _txt(c, split + 120, top - 2 * row_h - 12, _fmt_date(_safe(lambda: ev.fecha_ultimo_dia_laboral)), 8)

    # =========================
    # 4) ANTECEDENTES
    # =========================
    y -= 10
    y -= LAYOUT_A1["sec4_h"]
    _title_bar(c, X, y + LAYOUT_A1["sec4_h"] - 18, W, 18, "4. ANTECEDENTES")
    _rect(c, X, y, W, LAYOUT_A1["sec4_h"] - 18)

    top = y + (LAYOUT_A1["sec4_h"] - 18)
    # 4 filas
    row_h = (LAYOUT_A1["sec4_h"] - 18) / 4
    for i in range(1, 4):
        _line(c, X, top - row_h * i, X + W, top - row_h * i)

    _txt(c, X + 6, top - 12, "Clínico-quirúrgicos:", 8, True)
    _txt(c, X + 6, top - row_h - 12, "Familiares:", 8, True)

    _txt(c, X + 6, top - 2 * row_h - 12, "Requiere transfusiones:", 8, True)
    _checkbox(c, X + 150, top - 2 * row_h - 18, checked=(ev and bool(ev.requiere_transfusiones)))
    _txt(c, X + 162, top - 2 * row_h - 12, "Sí", 8)
    _checkbox(c, X + 185, top - 2 * row_h - 18, checked=(ev and ev.requiere_transfusiones is False))
    _txt(c, X + 197, top - 2 * row_h - 12, "No", 8)

    _txt(c, X + 240, top - 2 * row_h - 12, "Tratamiento hormonal:", 8, True)
    _checkbox(c, X + 375, top - 2 * row_h - 18, checked=(ev and bool(ev.tratamiento_hormonal)))
    _txt(c, X + 387, top - 2 * row_h - 12, "Sí", 8)

    _txt(c, X + 430, top - 2 * row_h - 12, "¿Cuál?:", 8, True)

    # gineco obstétricos
    _txt(c, X + 6, top - 3 * row_h - 12, "FUM / Gestas / Partos / Cesáreas / Abortos / Planificación:", 8, True)

    if ev:
        _txt_wrap(c, X + 120, top - 12, _safe(lambda: ev.antecedentes_clinico_quirurgicos), w=W - 130, size=8, leading=9, max_lines=1)
        _txt_wrap(c, X + 80, top - row_h - 12, _safe(lambda: ev.antecedentes_familiares), w=W - 90, size=8, leading=9, max_lines=1)
        _txt(c, X + 470, top - 2 * row_h - 12, _safe(lambda: ev.tratamiento_hormonal_cual), 8)

        fum = _fmt_date(_safe(lambda: ev.fecha_ultima_menstruacion))
        plan = _safe(lambda: ev.planificacion_familiar, "")
        plan_cual = _safe(lambda: ev.planificacion_familiar_cual, "")
        obst = f"FUM: {fum} | G:{_safe(lambda: ev.gestas)} P:{_safe(lambda: ev.partos)} C:{_safe(lambda: ev.cesareas)} A:{_safe(lambda: ev.abortos)} | PF:{plan} {plan_cual}"
        _txt_wrap(c, X + 10, top - 3 * row_h - 28, obst, w=W - 20, size=8, leading=9, max_lines=2)

    # =========================
    # 5) HÁBITOS / ESTILOS
    # =========================
    y -= 10
    y -= LAYOUT_A1["sec5_h"]
    _title_bar(c, X, y + LAYOUT_A1["sec5_h"] - 18, W, 18, "5. HÁBITOS Y ESTILOS")
    _rect(c, X, y, W, LAYOUT_A1["sec5_h"] - 18)

    top = y + (LAYOUT_A1["sec5_h"] - 18)
    row_h = (LAYOUT_A1["sec5_h"] - 18) / 2
    _line(c, X, top - row_h, X + W, top - row_h)
    split = X + W * 0.50
    _line(c, split, y, split, top)

    _txt(c, X + 6, top - 12, "Tabaco / Alcohol / Drogas:", 8, True)
    _txt(c, split + 6, top - 12, "Actividad física:", 8, True)

    if ev:
        hab = f"Tabaco: {_safe(lambda: ev.tabaco_detalle)} | Alcohol: {_safe(lambda: ev.alcohol_detalle)} | Drogas: {_safe(lambda: ev.drogas_detalle)}"
        _txt_wrap(c, X + 6, top - 28, hab, w=split - X - 12, size=8, leading=9, max_lines=2)

        af = f"{_safe(lambda: ev.actividad_fisica)} / {_safe(lambda: ev.actividad_fisica_tiempo)}"
        _txt_wrap(c, split + 6, top - 28, af, w=(X + W) - split - 12, size=8, leading=9, max_lines=2)

    # =========================
    # 6) SIGNOS VITALES / ANTROPOMETRÍA
    # =========================
    y -= 10
    y -= LAYOUT_A1["sec6_h"]
    _title_bar(c, X, y + LAYOUT_A1["sec6_h"] - 18, W, 18, "6. SIGNOS VITALES Y MEDIDAS")
    _rect(c, X, y, W, LAYOUT_A1["sec6_h"] - 18)

    top = y + (LAYOUT_A1["sec6_h"] - 18)
    row_h = (LAYOUT_A1["sec6_h"] - 18) / 2
    _line(c, X, top - row_h, X + W, top - row_h)

    # 9 columnas
    cols = [X + W * p for p in (0.11, 0.22, 0.33, 0.44, 0.55, 0.66, 0.77, 0.88)]
    for cx in cols:
        _line(c, cx, y, cx, top)

    labels = ["T°", "PA", "FC", "FR", "SpO2", "Peso", "Talla", "IMC", "Per. Abd."]
    xs = [X] + cols + [X + W]
    for i in range(9):
        _txt(c, xs[i] + 4, top - 12, labels[i], 7, True)

    if ev:
        vals = [
            _safe(lambda: ev.temperatura_c),
            _safe(lambda: ev.presion_arterial),
            _safe(lambda: ev.frecuencia_cardiaca),
            _safe(lambda: ev.frecuencia_respiratoria),
            _safe(lambda: ev.saturacion_oxigeno),
            _safe(lambda: ev.peso_kg),
            _safe(lambda: ev.talla_cm),
            _safe(lambda: ev.imc),
            _safe(lambda: ev.perimetro_abdominal_cm),
        ]
        for i in range(9):
            _txt(c, xs[i] + 4, top - row_h - 12, vals[i], 8)

    # =========================
    # 7) EXAMEN FÍSICO (texto por sistemas)
    # =========================
    y -= 10
    y -= LAYOUT_A1["sec7_h"]
    _title_bar(c, X, y + LAYOUT_A1["sec7_h"] - 18, W, 18, "7. EXAMEN FÍSICO")
    _rect(c, X, y, W, LAYOUT_A1["sec7_h"] - 18)

    top = y + (LAYOUT_A1["sec7_h"] - 18)
    # dos columnas
    split = X + W * 0.50
    _line(c, split, y, split, top)
    # 7 filas aprox
    rows = 7
    row_h = (LAYOUT_A1["sec7_h"] - 18) / rows
    for i in range(1, rows):
        _line(c, X, top - row_h * i, X + W, top - row_h * i)

    left_labels = ["Cabeza", "Ojos", "Oídos", "Nariz", "Boca", "Faringe", "Cuello"]
    right_labels = ["Tórax", "Pulmones", "Corazón", "Abdomen", "Columna", "Ext. sup.", "Ext. inf."]

    for i in range(rows):
        _txt(c, X + 6, top - row_h * i - 12, left_labels[i] + ":", 7, True)
        _txt(c, split + 6, top - row_h * i - 12, right_labels[i] + ":", 7, True)

    if ev:
        left_vals = [
            _safe(lambda: ev.examen_cabeza),
            _safe(lambda: ev.examen_ojos),
            _safe(lambda: ev.examen_oidos),
            _safe(lambda: ev.examen_nariz),
            _safe(lambda: ev.examen_boca),
            _safe(lambda: ev.examen_faringe),
            _safe(lambda: ev.examen_cuello),
        ]
        right_vals = [
            _safe(lambda: ev.examen_torax),
            _safe(lambda: ev.examen_pulmones),
            _safe(lambda: ev.examen_corazon),
            _safe(lambda: ev.examen_abdomen),
            _safe(lambda: ev.examen_columna),
            _safe(lambda: ev.examen_extremidades_superiores),
            _safe(lambda: ev.examen_extremidades_inferiores),
        ]
        for i in range(rows):
            _txt_wrap(c, X + 65, top - row_h * i - 12, left_vals[i], w=(split - (X + 70)), size=7, leading=8, max_lines=2)
            _txt_wrap(c, split + 75, top - row_h * i - 12, right_vals[i], w=((X + W) - (split + 80)), size=7, leading=8, max_lines=2)

        # línea final extra: piel / neurológico / pelvis / obs.
        # (si tu formato lo incluye en otra hoja, puedes moverlo a anexo2)
        # aquí lo coloco en el último espacio disponible:
        extra_y = y + 8
        _txt(c, X + 6, extra_y + 2, "Piel / Neurológico / Pelvis / Observación:", 7, True)
        extra = f"Piel: {_safe(lambda: ev.examen_piel)} | Neuro: {_safe(lambda: ev.examen_neurologico)} | Pelvis: {_safe(lambda: ev.examen_pelvis_genitales)} | Obs: {_safe(lambda: ev.examen_observacion)}"
        _txt_wrap(c, X + 220, extra_y + 2, extra, w=W - 230, size=7, leading=8, max_lines=2)

    # =========================
    # 8) APTITUD / RETIRO / RECOMENDACIONES
    # =========================
    y -= 10
    y -= LAYOUT_A1["sec8_h"]
    _title_bar(c, X, y + LAYOUT_A1["sec8_h"] - 18, W, 18, "8. APTITUD / RETIRO / RECOMENDACIONES")
    _rect(c, X, y, W, LAYOUT_A1["sec8_h"] - 18)

    top = y + (LAYOUT_A1["sec8_h"] - 18)
    # 3 filas
    row_h = (LAYOUT_A1["sec8_h"] - 18) / 3
    _line(c, X, top - row_h, X + W, top - row_h)
    _line(c, X, top - 2 * row_h, X + W, top - 2 * row_h)

    _txt(c, X + 6, top - 12, "Aptitud médica:", 8, True)
    _txt(c, X + 6, top - row_h - 12, "Detalle / Observaciones:", 8, True)
    _txt(c, X + 6, top - 2 * row_h - 12, "Recomendaciones / Tratamiento:", 8, True)

    # check aptitud
    ax = X + 110
    ay = top - 22
    opts = [("APTO", "Apto"), ("APTO_OBSERVACION", "Apto obs."), ("APTO_LIMITACIONES", "Apto limit."), ("NO_APTO", "No apto")]
    for i, (k, lbl) in enumerate(opts):
        _checkbox(c, ax + i * 105, ay, checked=(ev and ev.aptitud_medica == k))
        _txt(c, ax + 14 + i * 105, ay + 2, lbl, 7)

    if ev:
        _txt_wrap(c, X + 170, top - row_h - 12, _safe(lambda: ev.aptitud_detalle_observaciones), w=W - 180, size=8, leading=9, max_lines=2)
        _txt_wrap(c, X + 200, top - 2 * row_h - 12, _safe(lambda: ev.recomendaciones_tratamiento), w=W - 210, size=8, leading=9, max_lines=2)

    # Footer mini
    _txt(c, X + 6, y - 10, "Documento generado por sistema (vectorial).", 7)

# =========================================================
# LAYOUT ANEXO 2 (tablas N) - ajustable 1 sola vez
# =========================================================
LAYOUT_A2 = {
    "margin": 26,
    "header_h": 40,

    # Cada bloque:
    # y_top = coordenada superior de la tabla (desde arriba hacia abajo)
    # row_h = alto de fila
    # max_rows = filas visibles por página en ese bloque
    "blocks": [
        {
            "key": "antecedentes",
            "title": "2.1 Antecedentes laborales (N)",
            "row_h": 16,
            "max_rows": 6,
            "cols": [
                ("empresa", 0.00, 0.14),
                ("puesto", 0.14, 0.14),
                ("actividad", 0.28, 0.20),
                ("tiempo", 0.48, 0.10),
                ("riesgos", 0.58, 0.12),
                ("epp", 0.70, 0.10),
                ("observaciones", 0.80, 0.20),
            ]
        },
        {
            "key": "incidentes",
            "title": "2.2 Incidentes / accidentes / enfermedades ocupacionales (N)",
            "row_h": 16,
            "max_rows": 5,
            "cols": [
                ("puesto_trabajo", 0.00, 0.18),
                ("actividad_desempenada", 0.18, 0.22),
                ("fecha", 0.40, 0.12),
                ("descripcion", 0.52, 0.20),
                ("calificado_por_instituto", 0.72, 0.06),
                ("reubicacion", 0.78, 0.06),
                ("observaciones", 0.84, 0.16),
            ]
        },
        {
            "key": "actividades",
            "title": "2.3 Actividades extralaborales (N)",
            "row_h": 16,
            "max_rows": 5,
            "cols": [
                ("tipo_actividad", 0.00, 0.40),
                ("frecuencia", 0.40, 0.20),
                ("observaciones", 0.60, 0.40),
            ]
        },
        {
            "key": "examenes",
            "title": "2.4 Exámenes generales / específicos (N)",
            "row_h": 16,
            "max_rows": 5,
            "cols": [
                ("nombre_examen", 0.00, 0.30),
                ("fecha", 0.30, 0.12),
                ("resultados", 0.42, 0.28),
                ("observaciones", 0.70, 0.30),
            ]
        },
        {
            "key": "diagnosticos",
            "title": "2.5 Diagnósticos (N)",
            "row_h": 16,
            "max_rows": 6,
            "cols": [
                ("cie10", 0.00, 0.12),
                ("descripcion", 0.12, 0.70),
                ("presuntivo", 0.82, 0.09),
                ("definitivo", 0.91, 0.09),
            ]
        },
    ],

    # Separación vertical entre bloques
    "gap": 14,

    # Fuente
    "font_size": 7,
    "title_size": 9,
}


def _draw_table_grid(c, x, y_top, w, row_h, n_rows, col_xs, lw=0.6):
    """
    Tabla desde y_top hacia abajo.
    col_xs: separadores verticales (x absolutos) dentro de la tabla.
    """
    _rect(c, x, y_top - row_h * n_rows, w, row_h * n_rows, lw=lw)
    for i in range(1, n_rows):
        _line(c, x, y_top - row_h * i, x + w, y_top - row_h * i, lw=lw)
    for cx in col_xs:
        _line(c, cx, y_top, cx, y_top - row_h * n_rows, lw=lw)


def _print_rows_in_table(c, rows, x, y_top, row_h, col_defs, font_size=7, max_rows=6):
    """
    col_defs: lista de dict con {key, x, w}
    Imprime hasta max_rows.
    Retorna printed_count.
    """
    printed = 0
    y_text = y_top - row_h + 4
    for r in rows[:max_rows]:
        for col in col_defs:
            val = r.get(col["key"], "")
            # normaliza bool como X
            if isinstance(val, bool):
                val = "X" if val else ""
            # fechas
            if hasattr(val, "strftime"):
                val = val.strftime("%Y-%m-%d")
            _txt_wrap(c, col["x"] + 2, y_text, val, w=col["w"] - 4, size=font_size, leading=8, max_lines=1)
        printed += 1
        y_text -= row_h
    return printed


def draw_anexo2(c, ev, state=None):
    """
    Dibuja 1 página del ANEXO 2.
    state mantiene offsets por bloque para paginación.
    Retorna (has_more, state)
    """
    if state is None:
        state = {"offsets": {}}

    offsets = state.setdefault("offsets", {})
    for b in LAYOUT_A2["blocks"]:
        offsets.setdefault(b["key"], 0)

    M = LAYOUT_A2["margin"]
    X = M
    W = PAGE_W - 2 * M
    y = PAGE_H - M

    # Header
    y -= LAYOUT_A2["header_h"]
    _rect(c, X, y, W, LAYOUT_A2["header_h"])
    _txt(c, X + 10, y + 18, "ANEXO 2 - REGISTROS COMPLEMENTARIOS (FEMO)", 11, True)

    y -= 10

    def qlist(key):
        if key == "antecedentes":
            return list(ev.antecedentes_laborales.filter(status=True).values(
                "id", "empresa", "puesto", "actividad", "tiempo", "riesgos", "epp", "observaciones"
            ))
        if key == "incidentes":
            rows = list(ev.incidentes_ocupacionales.filter(status=True).values(
                "id", "puesto_trabajo", "actividad_desempenada", "fecha", "descripcion",
                "calificado_por_instituto", "reubicacion", "observaciones"
            ))
            for r in rows:
                r["calificado_por_instituto"] = bool(r.get("calificado_por_instituto"))
                r["reubicacion"] = bool(r.get("reubicacion"))
            return rows
        if key == "actividades":
            return list(ev.actividades_extralaborales.filter(status=True).values(
                "id", "tipo_actividad", "frecuencia", "observaciones"
            ))
        if key == "examenes":
            return list(ev.examenes.filter(status=True).values(
                "id", "nombre_examen", "fecha", "resultados", "observaciones"
            ))
        if key == "diagnosticos":
            rows = list(ev.diagnosticos.filter(status=True).values(
                "id", "cie10", "descripcion", "presuntivo", "definitivo"
            ))
            for r in rows:
                r["presuntivo"] = bool(r.get("presuntivo"))
                r["definitivo"] = bool(r.get("definitivo"))
            return rows
        return []

    has_more_any = False

    # Dibuja bloques en cascada
    for block in LAYOUT_A2["blocks"]:
        key = block["key"]
        title = block["title"]
        row_h = block["row_h"]
        max_rows = block["max_rows"]

        # título
        _title_bar(c, X, y - 18, W, 18, title)
        y -= 22

        all_rows = qlist(key)
        start = offsets[key]
        rows = all_rows[start:]

        # columnas absolutas
        col_defs = []
        col_xs = []
        for (k, rel_x, rel_w) in block["cols"]:
            cx = X + W * rel_x
            cw = W * rel_w
            col_defs.append({"key": k, "x": cx, "w": cw})
        # separadores (todo menos el primero)
        running = X
        for (k, rel_x, rel_w) in block["cols"][:-1]:
            running = X + W * (rel_x + rel_w)
            col_xs.append(running)

        # tabla
        _draw_table_grid(c, X, y, W, row_h, max_rows, col_xs, lw=0.6)

        # encabezados de columnas (fila 1 “visual” arriba)
        # los pones encima de la tabla, estilo sencillo
        header_y = y + 4
        for col in col_defs:
            _txt(c, col["x"] + 2, header_y, col["key"].replace("_", " ").title(), 6, True)

        # imprime filas
        printed = _print_rows_in_table(
            c,
            rows=rows,
            x=X,
            y_top=y,
            row_h=row_h,
            col_defs=col_defs,
            font_size=LAYOUT_A2["font_size"],
            max_rows=max_rows
        )
        offsets[key] += printed

        # mueve cursor debajo de la tabla
        y -= row_h * max_rows
        y -= LAYOUT_A2["gap"]

        # ¿queda data para este bloque?
        if offsets[key] < len(all_rows):
            has_more_any = True

        # si ya no hay espacio para el siguiente bloque, corta página (lo marca como more)
        # (esto es protección adicional)
        if y < 90:
            has_more_any = True
            break

    return has_more_any, state

# =========================================================
# DRAW_ANEXO3 (VECTORIAL)
# =========================================================
LAYOUT_A3 = {
    "margin": 26,
    "header_h": 46,

    "sec_cert_h": 140,    # aptitud + observaciones + recomendaciones
    "sec_retiro_h": 70,   # retiro (si aplica)
    "sec_firmas_h": 150,  # firmas/huellas/codigo medico
    "footer_h": 24,
}


def draw_anexo3(c, ev=None):
    """
    ANEXO 3: CIERRE / CERTIFICACIÓN / FIRMAS (vectorial).
    - Incluye certificado (aptitud + observaciones + recomendaciones + firma/huella)
    - Incluye firma y sello del profesional
    - Incluye bloque retiro (si aplica)
    """
    M = LAYOUT_A3["margin"]
    X = M
    W = PAGE_W - 2 * M
    y = PAGE_H - M

    # ========== HEADER ==========
    y -= LAYOUT_A3["header_h"]
    _rect(c, X, y, W, LAYOUT_A3["header_h"])
    _txt(c, X + 10, y + 26, "EVALUACIÓN MÉDICA OCUPACIONAL (FEMO)", 12, True)
    _txt(c, X + 10, y + 10, "FORMULARIO - ANEXO 3 (CIERRE / CERTIFICACIÓN / FIRMAS)", 9, True)

    # ========== CERTIFICADO ==========
    y -= 10
    y -= LAYOUT_A3["sec_cert_h"]
    _title_bar(c, X, y + LAYOUT_A3["sec_cert_h"] - 18, W, 18, "3.1 CERTIFICADO DE APTITUD MÉDICA")
    _rect(c, X, y, W, LAYOUT_A3["sec_cert_h"] - 18)

    top = y + (LAYOUT_A3["sec_cert_h"] - 18)
    # 4 filas
    rows = 4
    row_h = (LAYOUT_A3["sec_cert_h"] - 18) / rows
    for i in range(1, rows):
        _line(c, X, top - row_h * i, X + W, top - row_h * i)

    # Fila 1: Fecha emisión + Aptitud (checkboxes)
    split = X + W * 0.35
    _line(c, split, top, split, top - row_h)

    _txt(c, X + 6, top - 12, "Fecha emisión:", 8, True)
    _txt(c, split + 6, top - 12, "Aptitud médica:", 8, True)

    # Check aptitud
    ax = split + 90
    ay = top - 22
    opts = [("APTO", "Apto"),
            ("APTO_OBSERVACION", "Apto obs."),
            ("APTO_LIMITACIONES", "Apto limit."),
            ("NO_APTO", "No apto")]
    for i, (k, lbl) in enumerate(opts):
        _checkbox(c, ax + i * 105, ay, checked=(ev and _safe(lambda: ev.aptitud_medica, "") == k))
        _txt(c, ax + 14 + i * 105, ay + 2, lbl, 7)

    # Fila 2: Observaciones
    _txt(c, X + 6, top - row_h - 12, "Detalle / Observaciones:", 8, True)

    # Fila 3: Recomendaciones
    _txt(c, X + 6, top - 2 * row_h - 12, "Recomendaciones / Tratamiento:", 8, True)

    # Fila 4: Firma/huella trabajador
    _txt(c, X + 6, top - 3 * row_h - 12, "Firma / huella trabajador:", 8, True)

    # Valores (desde modelo Certificado o desde ev)
    cert = None
    if ev:
        cert = _safe(lambda: ev.certificado, None)

    if cert:
        _txt(c, X + 90, top - 12, _fmt_date(_safe(lambda: cert.fecha_emision)), 8)
        _txt_wrap(c, X + 170, top - row_h - 12, _safe(lambda: cert.detalle_observaciones), w=W - 180, size=8, leading=9, max_lines=3)
        _txt_wrap(c, X + 200, top - 2 * row_h - 12, _safe(lambda: cert.recomendaciones), w=W - 210, size=8, leading=9, max_lines=3)
        _txt_wrap(c, X + 160, top - 3 * row_h - 12, _safe(lambda: cert.firma_huella_trabajador), w=W - 170, size=8, leading=9, max_lines=2)
    elif ev:
        # fallback por si aún no usas el OneToOne
        _txt(c, X + 90, top - 12, "", 8)
        _txt_wrap(c, X + 170, top - row_h - 12, _safe(lambda: ev.aptitud_detalle_observaciones), w=W - 180, size=8, leading=9, max_lines=3)
        _txt_wrap(c, X + 200, top - 2 * row_h - 12, _safe(lambda: ev.recomendaciones_tratamiento), w=W - 210, size=8, leading=9, max_lines=3)
        _txt_wrap(c, X + 160, top - 3 * row_h - 12, _safe(lambda: ev.firma_huella_trabajador), w=W - 170, size=8, leading=9, max_lines=2)

    # ========== RETIRO (SI APLICA) ==========
    y -= 10
    y -= LAYOUT_A3["sec_retiro_h"]
    _title_bar(c, X, y + LAYOUT_A3["sec_retiro_h"] - 18, W, 18, "3.2 RETIRO (SI APLICA)")
    _rect(c, X, y, W, LAYOUT_A3["sec_retiro_h"] - 18)

    top = y + (LAYOUT_A3["sec_retiro_h"] - 18)
    row_h = (LAYOUT_A3["sec_retiro_h"] - 18) / 2
    _line(c, X, top - row_h, X + W, top - row_h)

    _txt(c, X + 6, top - 12, "Se realiza evaluación por retiro:", 8, True)
    _checkbox(c, X + 205, top - 18, checked=(ev and bool(_safe(lambda: ev.retiro_se_realiza_evaluacion))))
    _txt(c, X + 220, top - 12, "Sí", 8)

    _txt(c, X + 260, top - 12, "Condición relacionada al trabajo:", 8, True)
    _checkbox(c, X + 455, top - 18, checked=(ev and bool(_safe(lambda: ev.retiro_condicion_relacionada_trabajo))))
    _txt(c, X + 470, top - 12, "Sí", 8)

    _txt(c, X + 6, top - row_h - 12, "Observación:", 8, True)
    if ev:
        _txt_wrap(c, X + 90, top - row_h - 12, _safe(lambda: ev.retiro_observacion), w=W - 100, size=8, leading=9, max_lines=2)

    # ========== FIRMAS ==========
    y -= 10
    y -= LAYOUT_A3["sec_firmas_h"]
    _title_bar(c, X, y + LAYOUT_A3["sec_firmas_h"] - 18, W, 18, "3.3 FIRMAS Y RESPONSABLES")
    _rect(c, X, y, W, LAYOUT_A3["sec_firmas_h"] - 18)

    top = y + (LAYOUT_A3["sec_firmas_h"] - 18)
    # 2 columnas grandes
    split = X + W * 0.5
    _line(c, split, y, split, top)

    # subdivisiones internas (3 filas)
    rows = 3
    row_h = (LAYOUT_A3["sec_firmas_h"] - 18) / rows
    for i in range(1, rows):
        _line(c, X, top - row_h * i, X + W, top - row_h * i)

    # Labels trabajador (izq)
    _txt(c, X + 6, top - 12, "Trabajador", 9, True)
    _txt(c, X + 6, top - row_h - 12, "Firma / Huella", 8, True)
    _txt(c, X + 6, top - 2 * row_h - 12, "Nombre y C.I.", 8, True)

    # Labels profesional (der)
    _txt(c, split + 6, top - 12, "Profesional de salud", 9, True)
    _txt(c, split + 6, top - row_h - 12, "Firma / Sello", 8, True)
    _txt(c, split + 6, top - 2 * row_h - 12, "Nombre / Código médico", 8, True)

    if ev:
        # Trabajador
        nom_trab = f"{_safe(lambda: ev.persona.razon_social)}"
        ci_trab = f"{_safe(lambda: ev.persona.identificacion)}"
        _txt_wrap(c, X + 120, top - 2 * row_h - 12, f"{nom_trab} / {ci_trab}".strip(" /"), w=(split - (X + 130)), size=8, leading=9, max_lines=2)

        # Firma trabajador (texto)
        _txt_wrap(c, X + 120, top - row_h - 12, _safe(lambda: ev.firma_huella_trabajador), w=(split - (X + 130)), size=8, leading=9, max_lines=2)

        # Profesional
        prof_nom = _safe(lambda: ev.profesional.persona.razon_social)
        prof_cod = _safe(lambda: ev.profesional.codigo_medico)
        _txt_wrap(c, split + 150, top - 2 * row_h - 12, f"{prof_nom} / {prof_cod}".strip(" /"), w=((X + W) - (split + 160)), size=8, leading=9, max_lines=2)

        # Firma/sello (texto)
        firma_sello = _safe(lambda: ev.profesional.firma_sello)
        _txt_wrap(c, split + 120, top - row_h - 12, firma_sello, w=((X + W) - (split + 130)), size=8, leading=9, max_lines=3)

    # ========== FOOTER ==========
    y -= 8
    _txt(c, X + 6, y, "Documento generado por sistema (vectorial, sin imágenes).", 7)


# =========================================================
# FUNCIÓN FINAL COMPLETA (ANEXO 1 + ANEXO 2 (N PÁGINAS) + ANEXO 3)
# =========================================================
# IMPORTANTE: draw_anexo1 y draw_anexo2 deben existir (los que ya te pasé).
# Si los tienes en otro archivo, solo impórtalos.

def generar_pdf_femo_completo(output_path, ev):
    """
    Genera un PDF FEMO COMPLETO:
      - Anexo 1 (1 página)
      - Anexo 2 (N páginas, según registros)
      - Anexo 3 (1 página)

    output_path: ruta destino .pdf
    ev: instancia EvaluacionMedicaOcupacional
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=A4)

    # ---- ANEXO 1 ----
    draw_anexo1(c, ev)   # <-- tu función ya hecha
    c.showPage()

    # ---- ANEXO 2 (N páginas) ----
    state = {}
    while True:
        has_more, state = draw_anexo2(c, ev, state)  # <-- tu función ya hecha
        c.showPage()
        if not has_more:
            break

    # ---- ANEXO 3 ----
    draw_anexo3(c, ev)
    c.showPage()

    c.save()
    return output_path