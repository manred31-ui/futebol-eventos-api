"""
Persistencia del historial GPS individual de jugadores.

Este módulo:
- guarda los registros preparados por player_report.py
- evita duplicar un jugador dentro del mismo partido
- permite recuperar el historial de un jugador
- utiliza la capa de persistencia existente del proyecto
"""

from __future__ import annotations

from typing import Any

import persistence as _persistence


HISTORY_KEY_PREFIX = "player_gps_history"


def _history_key() -> str:
    """Genera una clave de historial aislada por organización."""
    return _persistence._org_key(HISTORY_KEY_PREFIX)


def cargar_historial() -> list[dict[str, Any]]:
    """
    Carga todos los registros históricos guardados.

    Si todavía no existe historial, devuelve una lista vacía.
    """
    try:
        datos = _persistence._get_store().get(_history_key())

        if isinstance(datos, list):
            return datos

        return []

    except Exception:
        return []


def guardar_registros_partido(
    registros: list[dict[str, Any]],
) -> int:
    """
    Guarda los registros de un partido.

    Usa record_key para que volver a cargar el mismo partido
    no cree duplicados.

    Devuelve la cantidad total de registros almacenados.
    """

    if not registros:
        return len(cargar_historial())

    historial = cargar_historial()

    indice = {}

    for registro in historial:
        clave = registro.get("record_key")

        if clave:
            indice[str(clave)] = registro

    for registro in registros:
        clave = registro.get("record_key")

        if not clave:
            continue

        indice[str(clave)] = registro

    nuevo_historial = list(indice.values())

    try:
        ok = _persistence._get_store().set(
            _history_key(),
            nuevo_historial,
        )

        if not ok:
            return len(historial)

    except Exception:
        return len(historial)

    return len(nuevo_historial)


def obtener_historial_jugador(
    player_id: str | int | None = None,
    player_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    Devuelve el historial de un jugador.

    Prioriza player_id cuando está disponible.
    Si no existe, utiliza el nombre.
    """

    historial = cargar_historial()

    if player_id is not None:
        player_id_str = str(player_id)

        resultados = [
            registro
            for registro in historial
            if registro.get("player_id") is not None
            and str(registro.get("player_id")) == player_id_str
        ]

        if resultados:
            return resultados

    if player_name:
        nombre = str(player_name).strip().lower()

        return [
            registro
            for registro in historial
            if str(registro.get("player_name", "")).strip().lower()
            == nombre
        ]

    return []


def contar_registros() -> int:
    """Devuelve el número total de registros históricos."""
    return len(cargar_historial())
