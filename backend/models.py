"""
models.py - Modelos de datos (Pydantic) usados por la API.
"""

from typing import Optional

from pydantic import BaseModel


class BusPosition(BaseModel):
    bus_id: str
    ruta_id: str
    lat: float
    lng: float
    velocidad_kmh: float
    siguiente_parada_index: int
    ocupacion: str  # "vacio" | "medio" | "lleno"


class OcupacionActualizar(BaseModel):
    """
    Cuerpo que envía el pipeline de cámara/YOLO para actualizar la
    ocupación real de un bus. Acepta DOS formas, según lo que tengas
    disponible en tu script de visión:

      1) Ya clasificaste tú mismo:      {"ocupacion": "lleno"}
      2) Solo tienes el conteo bruto:   {"conteo_personas": 27}

    Si llegan ambos, "ocupacion" manda (se asume ya validado por tu
    modelo). Si solo llega "conteo_personas", el backend lo clasifica
    usando los umbrales de services/occupancy_service.py.
    """
    ocupacion: Optional[str] = None
    conteo_personas: Optional[int] = None
