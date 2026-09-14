"""
Motor de reportes individuales de jugadores.

Este módulo toma las métricas que ya calcula el sistema
y las convierte en un formato estable para construir
los reportes GPS individuales.

IMPORTANTE:
- No recalcula métricas.
- No cambia zonas ni umbrales.
- No depende de Streamlit.
- No guarda información todavía.
"""

from __future__ import annotations

from typing import Any


# ============================================================
# MÉTRICAS OFICIALES DEL PLAYER GPS REPORT
# ============================================================

REPORT_METRICS = {
    "player_load": "PlayerLoad",
    "m_min": "M/min",
    "max_velocity": "Velocidade Máx (km/h)",
    "high_speed_distance": "Dist. > 19 km/h (m)",
    "sprint_distance": "Dist. > 24 km/h (m)",
    "accelerations": "Acelerações (>3 m/s²)",
    "decelerations": "Desacelerações (<-3 m/s²)",
    "total_distance": "Distância (m)",
}


# ============================================================
# UTILIDADES
# ============================================================

def _to_float(value: Any) -> float | None:
    """Convierte un valor a float sin romper si viene vacío."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    """Convierte un valor a entero sin romper si viene vacío."""
    number = _to_float(value)

    if number is None:
        return None

    return int(round(number))


# ============================================================
# NORMALIZACIÓN DE UN PARTIDO
# ============================================================

def normalizar_metricas_jugador(
    metricas: dict[str, Any],
    activity_id: str | int | None = None,
    match_name: str | None = None,
    match_date: str | None = None,
    opponent: str | None = None,
    player_id: str | int | None = None,
) -> dict[str, Any]:
    """
    Convierte el diccionario actual de métricas del sistema
    en un registro estable para el historial del jugador.

    Las métricas originales NO se modifican.
    """

    return {
        "player_id": player_id,
        "player_name": metricas.get("Atleta"),
        "activity_id": activity_id,
        "match_name": match_name,
        "match_date": match_date,
        "opponent": opponent,

        # Contexto
        "position": metricas.get("Posição"),
        "team": metricas.get("Equipe"),
        "duration_min": _to_float(metricas.get("Duração (min)")),

        # ====================================================
        # LAS 8 MÉTRICAS DEL PLAYER GPS REPORT
        # ====================================================

        "player_load": _to_float(
            metricas.get(REPORT_METRICS["player_load"])
        ),

        "m_min": _to_float(
            metricas.get(REPORT_METRICS["m_min"])
        ),

        "max_velocity": _to_float(
            metricas.get(REPORT_METRICS["max_velocity"])
        ),

        "high_speed_distance": _to_float(
            metricas.get(REPORT_METRICS["high_speed_distance"])
        ),

        "sprint_distance": _to_float(
            metricas.get(REPORT_METRICS["sprint_distance"])
        ),

        "accelerations": _to_int(
            metricas.get(REPORT_METRICS["accelerations"])
        ),

        "decelerations": _to_int(
            metricas.get(REPORT_METRICS["decelerations"])
        ),

        "total_distance": _to_float(
            metricas.get(REPORT_METRICS["total_distance"])
        ),
    }


# ============================================================
# VALIDACIÓN
# ============================================================

def registro_valido(registro: dict[str, Any]) -> bool:
    """
    Comprueba si existe la información mínima necesaria
    para guardar un registro histórico.
    """

    if not registro.get("player_name"):
        return False

    if not registro.get("activity_id"):
        return False

    return True


# ============================================================
# IDENTIFICADOR ÚNICO
# ============================================================

def generar_clave_registro(registro: dict[str, Any]) -> str | None:
    """
    Genera una clave estable para evitar guardar dos veces
    el mismo jugador en el mismo partido.
    """

    activity_id = registro.get("activity_id")
    player_id = registro.get("player_id")

    if activity_id is None:
        return None

    if player_id is not None:
        return f"{activity_id}:{player_id}"

    player_name = registro.get("player_name")

    if not player_name:
        return None

    return f"{activity_id}:{player_name}"


# ============================================================
# PREPARAR REGISTRO
# ============================================================

def preparar_registro_partido(
    metricas: dict[str, Any],
    activity_id: str | int | None = None,
    match_name: str | None = None,
    match_date: str | None = None,
    opponent: str | None = None,
    player_id: str | int | None = None,
) -> dict[str, Any] | None:
    """
    Normaliza y valida las métricas de un jugador.

    Devuelve None si el registro no tiene la información
    mínima necesaria.
    """

    registro = normalizar_metricas_jugador(
        metricas=metricas,
        activity_id=activity_id,
        match_name=match_name,
        match_date=match_date,
        opponent=opponent,
        player_id=player_id,
    )

    if not registro_valido(registro):
        return None

    registro["record_key"] = generar_clave_registro(registro)

    return registro
