"""
simulator.py - Tarea de fondo que mueve los buses sobre su ruta.
"""

import asyncio

from data import BUSES_ESTADO, RUTAS
from geo import haversine_km

INTERVALO_SEGUNDOS = 2.0


async def mover_buses():
    """Cada INTERVALO_SEGUNDOS avanza cada bus un poquito sobre su ruta."""
    while True:
        for bus_id, estado in BUSES_ESTADO.items():
            puntos = RUTAS[estado["ruta_id"]]
            i = estado["segmento_actual"]

            if i >= len(puntos) - 1:
                # Llegó al final, reinicia el recorrido (loop demo)
                estado["segmento_actual"] = 0
                estado["progreso"] = 0.0
                continue

            p1, p2 = puntos[i], puntos[i + 1]
            dist_segmento_km = haversine_km(p1["lat"], p1["lng"], p2["lat"], p2["lng"])

            if dist_segmento_km == 0:
                estado["segmento_actual"] += 1
                continue

            # ¿Cuánto avanza en este intervalo según su velocidad?
            avance_km = (estado["velocidad_kmh"] / 3600) * INTERVALO_SEGUNDOS
            avance_fraccion = avance_km / dist_segmento_km

            estado["progreso"] += avance_fraccion

            if estado["progreso"] >= 1.0:
                estado["segmento_actual"] += 1
                estado["progreso"] = 0.0

        await asyncio.sleep(INTERVALO_SEGUNDOS)
