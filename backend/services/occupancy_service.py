"""
services/occupancy_service.py - Traduce datos reales de ocupación (de una
cámara, sensor, o conteo manual) al campo "ocupacion" de cada bus.

Este módulo es el punto de unión entre tu simulación y la realidad:
hoy BUSES_ESTADO[bus_id]["ocupacion"] está fijo en el código (data.py).
Cuando conectes una cámara real (ver services/yolo_service.py), en vez
de inventar el valor, llamas a `actualizar_ocupacion(bus_id, conteo)`
desde ese pipeline (o vía el endpoint POST /buses/{bus_id}/ocupacion)
y aquí se decide "vacio" / "medio" / "lleno".
"""

from typing import Optional

from data import BUSES_ESTADO

# ---------------------------------------------------------------------------
# Umbrales de clasificación por conteo de personas detectadas en el bus.
# AJUSTA estos números según la capacidad real de tus buses.
#   vacio:  0  - UMBRAL_VACIO
#   medio:  UMBRAL_VACIO+1 - UMBRAL_MEDIO
#   lleno:  más de UMBRAL_MEDIO
# ---------------------------------------------------------------------------
UMBRAL_VACIO = 15
UMBRAL_MEDIO = 35

OCUPACIONES_VALIDAS = {"vacio", "medio", "lleno"}


def clasificar_por_conteo(conteo_personas: int) -> str:
    if conteo_personas <= UMBRAL_VACIO:
        return "vacio"
    if conteo_personas <= UMBRAL_MEDIO:
        return "medio"
    return "lleno"


def actualizar_ocupacion(
    bus_id: str,
    ocupacion: Optional[str] = None,
    conteo_personas: Optional[int] = None,
) -> dict:
    """
    Actualiza BUSES_ESTADO[bus_id]["ocupacion"] a partir de:
      - un valor ya clasificado ("ocupacion"), o
      - un conteo bruto de personas ("conteo_personas") que se clasifica aquí.

    Devuelve el estado actualizado del bus (dict interno).
    Lanza ValueError si el bus no existe o el valor de ocupación es inválido.
    """
    estado = BUSES_ESTADO.get(bus_id)
    if estado is None:
        raise ValueError(f"Bus '{bus_id}' no encontrado")

    if ocupacion is not None:
        if ocupacion not in OCUPACIONES_VALIDAS:
            raise ValueError(f"Ocupación inválida: '{ocupacion}'")
        estado["ocupacion"] = ocupacion
    elif conteo_personas is not None:
        estado["ocupacion"] = clasificar_por_conteo(conteo_personas)
        estado["ultimo_conteo_personas"] = conteo_personas
    else:
        raise ValueError("Debes enviar 'ocupacion' o 'conteo_personas'")

    return estado
