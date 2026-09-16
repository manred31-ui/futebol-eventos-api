from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def _numero(valor):
    try:
        if valor is None or valor == "":
            return None
        return float(valor)
    except (TypeError, ValueError):
        return None


def _formato(valor, decimales=0):
    numero = _numero(valor)
    if numero is None:
        return "—"
    if decimales == 0:
        return f"{numero:,.0f}".replace(",", ".")
    return f"{numero:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_pdf_player_gps(
    actual,
    registros_partido,
    nombre,
    posicion,
):
    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=2 * mm,
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4 * mm,
    )

    seccion = ParagraphStyle(
        "Seccion",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        spaceBefore=3 * mm,
        spaceAfter=2 * mm,
    )

    normal = ParagraphStyle(
        "NormalGPS",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10,
    )

    elementos = []

    elementos.append(Paragraph("PLAYER GPS REPORT", titulo))
    elementos.append(
        Paragraph(
            f"<b>{nombre}</b><br/>{posicion}",
            subtitulo,
        )
    )

    partido = actual.get("match_name") or "Partido"
    minutos = actual.get("duration_min")

    elementos.append(
        Paragraph(
            f"<b>{partido}</b> &nbsp;&nbsp; | &nbsp;&nbsp; "
            f"<b>{_formato(minutos, 0)} min jugados</b>",
            normal,
        )
    )

    elementos.append(Paragraph("TU PARTIDO", seccion))

    metricas_principales = [
        ["Metros x minuto", f"{_formato(actual.get('m_min'), 1)} m/min"],
        ["Velocidad máxima", f"{_formato(actual.get('max_velocity'), 1)} km/h"],
        ["Distancia total", f"{_formato(actual.get('total_distance'))} m"],
        ["PlayerLoad", f"{_formato(actual.get('player_load'))} pts"],
    ]

    tabla_principal = Table(
        metricas_principales,
        colWidths=[55 * mm, 55 * mm],
    )

    tabla_principal.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elementos.append(tabla_principal)

    elementos.append(Paragraph("TUS 8 MÉTRICAS", seccion))

    metricas = [
        ("PlayerLoad", actual.get("player_load"), "pts"),
        ("Metros x minuto", actual.get("m_min"), "m/min"),
        ("Velocidad máxima", actual.get("max_velocity"), "km/h"),
        ("Distancia a alta velocidad", actual.get("high_speed_distance"), "m"),
        ("Sprint >25 km/h", actual.get("sprint_distance"), "m"),
        ("Aceleraciones", actual.get("accelerations"), ""),
        ("Desaceleraciones", actual.get("decelerations"), ""),
        ("Distancia total", actual.get("total_distance"), "m"),
    ]

    filas = []
    for i in range(0, len(metricas), 2):
        fila = []
        for nombre_metrica, valor, unidad in metricas[i:i + 2]:
            texto_valor = _formato(
                valor,
                1 if nombre_metrica in ("Metros x minuto", "Velocidad máxima") else 0,
            )
            fila.extend(
                [
                    Paragraph(
                        f"<b>{nombre_metrica}</b><br/>{texto_valor} {unidad}",
                        normal,
                    ),
                ]
            )
        filas.append(fila)

    tabla_metricas = Table(
        filas,
        colWidths=[87 * mm, 87 * mm],
    )

    tabla_metricas.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elementos.append(tabla_metricas)

    elementos.append(Paragraph("TUS HITOS", seccion))

    hitos = [
        f"Velocidad máxima: <b>{_formato(actual.get('max_velocity'), 1)} km/h</b>",
        f"Sprint >25 km/h: <b>{_formato(actual.get('sprint_distance'))} m</b>",
        f"Alta velocidad: <b>{_formato(actual.get('high_speed_distance'))} m</b>",
        f"Intensidad: <b>{_formato(actual.get('m_min'), 1)} m/min</b>",
    ]

    for hito in hitos:
        elementos.append(Paragraph(f"• {hito}", normal))

    elementos.append(Paragraph("TU EVOLUCIÓN", seccion))

    historial = [
        registro
        for registro in registros_partido
        if str(registro.get("player_name", "")).strip().lower()
        == str(nombre).strip().lower()
    ]

    historial = historial[-5:]

    datos_evolucion = [
        [
            "Partido",
            "Min",
            "m/min",
            "Vmax",
            "HSD",
            "Sprint",
        ]
    ]

    for registro in historial:
        datos_evolucion.append(
            [
                str(registro.get("match_name") or "Partido"),
                _formato(registro.get("duration_min")),
                _formato(registro.get("m_min"), 1),
                _formato(registro.get("max_velocity"), 1),
                _formato(registro.get("high_speed_distance")),
                _formato(registro.get("sprint_distance")),
            ]
        )

    tabla_evolucion = Table(
        datos_evolucion,
        colWidths=[72 * mm, 18 * mm, 23 * mm, 20 * mm, 20 * mm, 20 * mm],
    )

    tabla_evolucion.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    elementos.append(tabla_evolucion)

    elementos.append(Paragraph("TU FOCO", seccion))
    elementos.append(
        Paragraph(
            "Revisa tu evolución partido a partido y enfócate en las métricas "
            "que muestran una mayor diferencia respecto a tu referencia personal.",
            normal,
        )
    )

    documento.build(elementos)

    return buffer.getvalue()
