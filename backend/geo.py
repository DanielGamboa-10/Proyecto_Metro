"""
geo.py - Utilidades geográficas y de cálculo de tiempos.
"""

import math


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Distancia en línea recta entre dos coordenadas, en kilómetros."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def interpolar(p1: dict, p2: dict, t: float) -> dict:
    """t entre 0 y 1 -> punto intermedio entre p1 y p2."""
    return {
        "lat": p1["lat"] + (p2["lat"] - p1["lat"]) * t,
        "lng": p1["lng"] + (p2["lng"] - p1["lng"]) * t,
    }


def factor_hora_pico(hora: int) -> float:
    """Multiplica el tiempo de viaje en horas pico (más lento)."""
    if 6 <= hora <= 8 or 17 <= hora <= 19:
        return 1.4
    return 1.0
