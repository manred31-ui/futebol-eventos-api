from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


METRICAS = [
    ("player_load", "PlayerLoad", "pts"),
    ("m_min", "Metros x minuto", "m/min"),
    ("max_velocity", "Velocidad máxima", "km/h"),
    ("high_speed_distance", "Distancia a alta velocidad", "m"),
    ("sprint_distance", "Sprint >25 km/h", "m"),
    ("accelerations", "Aceleraciones", ""),
    ("decelerations", "Desaceleraciones", ""),
    ("total_distance", "Distancia total", "m"),
]


def _numero(valor: Any) -> float | None:
    try:
        if valor is None:
            return None
        return float(valor)
    except (TypeError, ValueError):
        return None


def _formato(valor: Any, decimales: int = 0) -> str:
    numero = _numero(valor)

    if numero is None:
        return "—"

    if decimales == 0:
        return f"{numero:,.0f}".replace(",", ".")
    return f"{numero:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _registro_mas_reciente(registros: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not registros:
        return None

    def clave(registro: dict[str, Any]):
        fecha = registro.get("match_date")
        if fecha is None:
            return ""
        return str(fecha)

    return sorted(registros, key=clave, reverse=True)[0]


def _estado_individual(valor: Any, referencia: Any) -> str:
    """
    Semáforo basado en el propio perfil del jugador.

    Verde:
        >= 105% de la referencia

    Amarillo:
        entre 90% y 105%

    Rojo:
        < 90%

    La referencia es la mediana histórica del jugador.
    """
    actual = _numero(valor)
    base = _numero(referencia)

    if actual is None or base is None or base == 0:
        return "🟡"

    relacion = actual / base

    if relacion >= 1.05:
        return "🟢"

    if relacion >= 0.90:
        return "🟡"

    return "🔴"


def _referencia_historica(
    historial: list[dict[str, Any]],
    clave: str,
) -> float | None:
    valores = []

    for registro in historial[-5:]:
        valor = _numero(registro.get(clave))

        if valor is not None:
            valores.append(valor)

    if not valores:
        return None

    return float(pd.Series(valores).median())


def _comparacion_texto(actual: Any, referencia: Any) -> str:
    valor = _numero(actual)
    base = _numero(referencia)

    if valor is None or base is None or base == 0:
        return "Sin referencia suficiente"

    diferencia = ((valor / base) - 1) * 100

    if diferencia > 5:
        return f"+{diferencia:.0f}% vs tu referencia"

    if diferencia < -5:
        return f"{diferencia:.0f}% vs tu referencia"

    return "En tu rango habitual"


def _es_participacion_corta(registro: dict[str, Any]) -> bool:
    duracion = _numero(registro.get("duration_min"))

    if duracion is None:
        return False

    return duracion < 20


def render_player_gps(
    player_name: str | None,
    historial: list[dict[str, Any]],
    current_record: dict[str, Any] | None = None,
) -> None:
    """Renderiza el informe individual Player GPS."""

    st.markdown("# 📋 PLAYER GPS REPORT")
    jugadores = sorted(
        {
            str(registro.get("player_name", "")).strip()
            for registro in historial
            if str(registro.get("player_name", "")).strip()
        }
        | (
            {str(current_record.get("player_name", "")).strip()}
            if current_record
            and str(current_record.get("player_name", "")).strip()
            else set()
        )
    )

    if jugadores:
        jugador_inicial = player_name if player_name in jugadores else jugadores[0]
        indice_inicial = jugadores.index(jugador_inicial)
        player_name = st.selectbox(
            "Jugador",
            jugadores,
            index=indice_inicial,
            key="player_gps_selector",
        )

    if current_record is not None:
        if (
            str(current_record.get("player_name", "")).strip().lower()
            != str(player_name).strip().lower()
        ):
            current_record = None

    if not player_name:
        st.info("Selecciona un jugador para ver su informe individual.")
        return

    nombre = str(player_name).strip().lower()

    registros = [
        registro
        for registro in historial
        if str(registro.get("player_name", "")).strip().lower() == nombre
    ]

    if current_record is not None:
        registros = [
            registro
            for registro in registros
            if registro.get("record_key") != current_record.get("record_key")
        ]
        registros.append(current_record)

    if not registros:
        st.warning(
            f"No hay historial GPS disponible todavía para {player_name}."
        )
        return

    registros = sorted(
    registros,
    key=lambda registro: int(
        __import__("re").search(
            r"Fecha\s+(\d+)",
            str(registro.get("match_name") or ""),
        ).group(1)
    )
    if __import__("re").search(
        r"Fecha\s+(\d+)",
        str(registro.get("match_name") or ""),
    )
    else 999,
)

    actual = current_record or registros[-1]

    registros_partido = [
        registro
        for registro in registros
        if (
            str(registro.get("session_type", "")).strip().lower() == "partido"
            or (
                not str(registro.get("session_type", "")).strip()
                and not str(registro.get("match_name", "")).strip().lower().startswith("entrenamiento")
            )
        )
    ]

    historico_anterior = [
        registro
        for registro in registros_partido
        if registro.get("record_key") != actual.get("record_key")
    ][-5:]

    nombre_mostrar = actual.get("player_name", player_name)
    posicion = actual.get("position") or "Posición no disponible"
    minutos = _numero(actual.get("duration_min"))
    fecha = actual.get("match_date") or "Fecha no disponible"
    partido = actual.get("match_name") or "Partido no identificado"
    rival = actual.get("opponent") or ""


    st.markdown(f"# ⚽ {nombre_mostrar}")
    st.markdown(f"### {posicion}")
    info_partido = f"**{fecha}** · {partido}"
    if rival:
        info_partido += f" · vs {rival}"

    if minutos is not None:
        info_partido += f" · **{_formato(minutos)} min**"

    st.caption(info_partido)

    if _es_participacion_corta(actual):
        st.warning(
            "⚠️ Participación corta: la lectura de este partido debe "
            "tomarse con cautela."
        )

    # ============================================================
    # TU PARTIDO
    # ============================================================

    st.markdown("## ⚽ TU PARTIDO")

    columnas = st.columns(4)

    principales = [
        ("m_min", "Metros x minuto", 1),
        ("max_velocity", "Velocidad máxima", 1),
        ("total_distance", "Distancia total", 0),
        ("player_load", "PlayerLoad", 0),
    ]

    for columna, (clave, titulo, decimales) in zip(columnas, principales):
        with columna:
            unidad = next(
                (unidad for k, _, unidad in METRICAS if k == clave),
                "",
            )

            valor = _formato(actual.get(clave), decimales)

            if unidad:
                valor = f"{valor} {unidad}"

            st.metric(titulo, valor)

    st.markdown("### Tus 8 métricas")

    filas = []

    for clave, titulo, unidad in METRICAS:
        valor = actual.get(clave)
        referencia = _referencia_historica(
            historico_anterior,
            clave,
        )

        if clave in ("max_velocity", "m_min"):
            decimales = 1
        else:
            decimales = 0

        valor_texto = _formato(valor, decimales)

        if unidad:
            valor_texto += f" {unidad}"

        filas.append(
            {
                "Métrica": titulo,
                "Tu partido": valor_texto,
                "Tu referencia": (
                    _formato(referencia, decimales)
                    if referencia is not None
                    else "—"
                ),
                "Lectura": _estado_individual(valor, referencia),
                "Comparación": _comparacion_texto(
                    valor,
                    referencia,
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(filas),
        use_container_width=True,
        hide_index=True,
    )

    # ============================================================
    # TUS HITOS
    # ============================================================

    st.markdown("## ⭐ TUS HITOS")

    max_vel = _numero(actual.get("max_velocity"))
    sprint = _numero(actual.get("sprint_distance"))
    hsd = _numero(actual.get("high_speed_distance"))
    mmin = _numero(actual.get("m_min"))

    hitos = []

    if max_vel is not None:
        hitos.append(
            f"Velocidad máxima: **{_formato(max_vel, 1)} km/h**"
        )

    if sprint is not None:
        hitos.append(
            f"Sprint >25 km/h: **{_formato(sprint)} m**"
        )

    if hsd is not None:
        hitos.append(
            f"Alta velocidad: **{_formato(hsd)} m**"
        )

    if mmin is not None:
        hitos.append(
            f"Intensidad: **{_formato(mmin, 1)} m/min**"
        )

    if hitos:
        for hito in hitos:
            st.write(f"• {hito}")
    else:
        st.info("No hay datos suficientes para destacar hitos.")

    # ============================================================
    # TU EVOLUCIÓN
    # ============================================================

    st.markdown("## 📈 TU EVOLUCIÓN")

    if len(registros_partido) < 2:
        st.info(
            "Todavía no hay suficientes partidos para mostrar una evolución."
        )
    else:
        evolucion = []

        for registro in registros_partido[-5:]:
            evolucion.append(
                {
                    "Fecha": registro.get("match_date") or "—",
                    "Partido": registro.get("match_name") or "—",
                    "Min jugados": _numero(registro.get("duration_min")),
                    "m/min": _numero(registro.get("m_min")),
                    "Vel. máx.": _numero(
                        registro.get("max_velocity")
                    ),
                    "HSD": _numero(
                        registro.get("high_speed_distance")
                    ),
                    "Sprint": _numero(
                        registro.get("sprint_distance")
                    ),
                    "Distancia": _numero(
                        registro.get("total_distance")
                    ),
                }
            )

        df_evolucion = pd.DataFrame(evolucion)

        st.dataframe(
            df_evolucion,
            use_container_width=True,
            hide_index=True,
        )

    # ============================================================
    # TU FOCO
    # ============================================================

    st.markdown("## 🎯 TU FOCO")

    focos = []

    for clave, titulo, unidad in METRICAS:
        referencia = _referencia_historica(
            historico_anterior,
            clave,
        )
        actual_valor = _numero(actual.get(clave))
        base = _numero(referencia)

        if actual_valor is None or base is None or base == 0:
            continue

        diferencia = actual_valor / base

        if diferencia < 0.90:
            focos.append(titulo)

    if focos:
        st.warning(
            "Tus métricas que más se alejaron de tu referencia fueron: "
            + ", ".join(focos[:3])
            + "."
        )
    else:
        st.success(
            "Tu partido estuvo dentro de tu rango habitual "
            "en las métricas disponibles."
        )

    st.caption(
        "La comparación se realiza principalmente contra tu propio historial. "
        "Las desaceleraciones representan exposición de carga y no se "
        "interpretan automáticamente como algo bueno o malo."
    )
