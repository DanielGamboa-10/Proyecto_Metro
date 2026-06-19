"""
models.py - Modelos de datos (Pydantic) usados por la API.
"""

from pydantic import BaseModel


class BusPosition(BaseModel):
    bus_id: str
    ruta_id: str
    lat: float
    lng: float
    velocidad_kmh: float
    siguiente_parada_index: int
    ocupacion: str  # "vacio" | "medio" | "lleno" (lo conectas luego con YOLO)
