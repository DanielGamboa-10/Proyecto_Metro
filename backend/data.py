"""
data.py - Definición de rutas y estado inicial de los buses.

IMPORTANTE: estas coordenadas son APROXIMADAS (Terminal -> Cabecera -> Floridablanca).
Reemplázalas por puntos reales trazando la ruta en Google Maps:
click derecho sobre la calle -> "¿Qué hay aquí?" -> copias lat,lng.
Mientras más puntos pongas, más realista se ve el movimiento del bus.
"""

from typing import Dict, List

# Corredor troncal real de Metrolínea (orden oficial sur -> norte, según
# comunicados de Alcaldía de Bucaramanga / Metrolínea). Las coordenadas
# son ESTIMADAS siguiendo el trazado real de la Autopista Piedecuesta-
# Floridablanca-Bucaramanga: verifícalas en Google Maps / OpenStreetMap
# antes de la demo final (click derecho sobre el punto -> copiar lat,lng).
RUTAS: Dict[str, List[dict]] = {
    "troncal": [
        {"nombre": "Portal de Piedecuesta", "lat": 7.0231, "lng": -73.0539},
        {"nombre": "Estación Palmichal", "lat": 7.0420, "lng": -73.0670},
        {"nombre": "Estación Lagos", "lat": 7.0530, "lng": -73.0790},
        {"nombre": "Estación Cañaveral", "lat": 7.0650, "lng": -73.0850},
        {"nombre": "Estación Payador", "lat": 7.0730, "lng": -73.0900},
        {"nombre": "Estación Provenza", "lat": 7.0810, "lng": -73.0950},
        {"nombre": "Estación Diamante", "lat": 7.0890, "lng": -73.1000},
        {"nombre": "Estación La Isla", "lat": 7.0970, "lng": -73.1050},
        {"nombre": "Estación La Rosita", "lat": 7.1030, "lng": -73.1090},
        {"nombre": "Estación Chorreras", "lat": 7.1090, "lng": -73.1130},
        {"nombre": "Estación San Mateo", "lat": 7.1140, "lng": -73.1160},
        {"nombre": "Estación Quebradaseca", "lat": 7.1193, "lng": -73.1188},
        {"nombre": "Parque Estación UIS", "lat": 7.1340, "lng": -73.1198},
    ],
}

# Estado en memoria de cada bus (se muta en tiempo real por el simulador)
# Distribuidos a lo largo del corredor (13 estaciones, índices 0-12) para
# simular una flota real: buses espaciados en distintos tramos, con
# velocidades y ocupación variadas en vez de agrupados en un solo punto.
BUSES_ESTADO: Dict[str, dict]  = {
    
    "bus_01": {
        "ruta_id": "troncal",
        "segmento_actual": 0,   # arrancando en el Portal de Piedecuesta
        "progreso": 0.0,        # 0.0 a 1.0 dentro del segmento actual
        "velocidad_kmh": 26.0,
        "ocupacion": "medio",
    },
    "bus_02": {
        "ruta_id": "troncal",
        "segmento_actual": 2,
        "progreso": 0.45,
        "velocidad_kmh": 30.0,
        "ocupacion": "vacio",
    },
    "bus_03": {
        "ruta_id": "troncal",
        "segmento_actual": 4,
        "progreso": 0.1,
        "velocidad_kmh": 18.0,
        "ocupacion": "lleno",
    },
    "bus_04": {
        "ruta_id": "troncal",
        "segmento_actual": 6,
        "progreso": 0.7,
        "velocidad_kmh": 24.0,
        "ocupacion": "medio",
    },
    "bus_05": {
        "ruta_id": "troncal",
        "segmento_actual": 8,
        "progreso": 0.3,
        "velocidad_kmh": 21.0,
        "ocupacion": "lleno",
    },
    "bus_06": {
        "ruta_id": "troncal",
        "segmento_actual": 10,
        "progreso": 0.55,
        "velocidad_kmh": 27.0,
        "ocupacion": "vacio",
    },
}