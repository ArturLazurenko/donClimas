"""Genera el PDF de evidencia de la métrica de usabilidad (System Usability Scale)."""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

import logica

SALIDA = os.path.join(logica.BASE_DIR, "Reporte_Usabilidad_DonClimas.pdf")
LOGO = os.path.join(logica.BASE_DIR, "assets", "logo.png")


def generar_pdf(nombre_alumno: str, ruta: str = SALIDA) -> str:
    resultados = logica.cargar_sus()
    if not resultados:
        raise ValueError("Aún no hay evaluaciones SUS registradas. "
                         "Aplica el cuestionario (Ayuda > Evaluar usabilidad).")
    prom = sum(r["puntaje"] for r in resultados) / len(resultados)

    st = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=st["Title"], fontSize=18, textColor=colors.HexColor("#1b4f9c"))
    h2 = ParagraphStyle("h2", parent=st["Heading2"], textColor=colors.HexColor("#1b4f9c"))
    p = ParagraphStyle("p", parent=st["BodyText"], leading=14, alignment=4)

    doc = SimpleDocTemplate(ruta, pagesize=letter, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title="Reporte de usabilidad - Don Climas", author=nombre_alumno)
    s = []
    if os.path.exists(LOGO):
        s.append(Image(LOGO, width=3 * cm, height=3.13 * cm))
    s += [
        Paragraph("Reporte de usabilidad: Don Climas", h1),
        Paragraph(f"Sistema de monitoreo meteorológico para transporte terrestre<br/>"
                  f"Alumno: {nombre_alumno} &nbsp;|&nbsp; Fecha: {datetime.now():%d/%m/%Y}",
                  ParagraphStyle("c", parent=p, alignment=1)),
        Spacer(1, 10),
        Paragraph("1. Métrica seleccionada: System Usability Scale (SUS)", h2),
        Paragraph(
            "La System Usability Scale (SUS, John Brooke, 1986) es un estándar de la industria "
            "para medir la usabilidad percibida de un sistema. Consiste en un cuestionario de "
            "10 afirmaciones que el usuario califica de 1 (totalmente en desacuerdo) a 5 "
            "(totalmente de acuerdo). Las afirmaciones alternan tono positivo (impares) y "
            "negativo (pares) para reducir el sesgo de respuesta, y cubren los tres atributos "
            "de la norma ISO 9241-11: eficacia, eficiencia y satisfacción.", p),
        Paragraph("2. Cálculo (escala 0 a 100)", h2),
        Paragraph(
            "Ítems impares: aportan (respuesta - 1). Ítems pares: aportan (5 - respuesta). "
            "Se suman las 10 aportaciones (0 a 40) y se multiplican por 2.5, obteniendo un "
            "puntaje de 0 a 100. El puntaje final del sistema es el promedio de todos los "
            "participantes. Interpretación: &ge;85 excelente, &ge;72 buena, &ge;68 aceptable "
            "(promedio SUS = 68), &ge;51 pobre, &lt;51 inaceptable.", p),
        Paragraph("3. Aplicación al proyecto", h2),
        Paragraph(
            "El cuestionario está integrado en la aplicación (menú Ayuda > Evaluar usabilidad "
            "(SUS)). Cada participante usó el sistema (inicio de sesión, captura de API Key y "
            "ciudad, consulta del clima, lectura del riesgo vial y de la imagen de condiciones) "
            "y contestó las 10 afirmaciones; la aplicación calcula y guarda el puntaje.", p),
        Spacer(1, 8),
    ]

    filas = [["#", "Participante", "Fecha", "Puntaje SUS", "Calificación"]]
    for i, r in enumerate(resultados, 1):
        filas.append([i, r["participante"], r["fecha"], f"{r['puntaje']:.1f}",
                      logica.clasificar_sus(r["puntaje"])])
    t = Table(filas, colWidths=[1 * cm, 4.2 * cm, 3.6 * cm, 2.6 * cm, 5.6 * cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b4f9c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4fb")]),
    ]))
    s += [Paragraph("4. Resultados", h2), t, Spacer(1, 12)]

    res = Table([[f"CALIFICACIÓN FINAL DE USABILIDAD: {prom:.1f} / 100",],
                 [f"{logica.clasificar_sus(prom)}  (n = {len(resultados)} participantes)"]],
                colWidths=[17 * cm])
    res.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e3f0ff")),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#1b4f9c")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    s += [res, Spacer(1, 12), Paragraph("5. Afirmaciones del cuestionario", h2)]
    for i, q in enumerate(logica.SUS_PREGUNTAS, 1):
        s.append(Paragraph(f"{i}. {q}", ParagraphStyle("q", parent=p, fontSize=9, leading=11,
                                                        alignment=0)))
    doc.build(s)
    return ruta


if __name__ == "__main__":
    print(generar_pdf("Artur"))
