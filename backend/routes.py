"""
routes.py - Endpoints de la API (separados del arranque de la app).
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from data import BUSES_ESTADO, RUTAS
from geo import factor_hora_pico, haversine_km, interpolar
from models import BusPosition

router = APIRouter()


def posicion_actual(bus_id: str) -> BusPosition:
    estado = BUSES_ESTADO.get(bus_id)
    if not estado:
        raise HTTPException(404, "Bus no encontrado")

    puntos = RUTAS[estado["ruta_id"]]
    i = min(estado["segmento_actual"], len(puntos) - 2)
    punto = interpolar(puntos[i], puntos[i + 1], estado["progreso"])

    return BusPosition(
        bus_id=bus_id,
        ruta_id=estado["ruta_id"],
        lat=punto["lat"],
        lng=punto["lng"],
        velocidad_kmh=estado["velocidad_kmh"],
        siguiente_parada_index=i + 1,
        ocupacion=estado["ocupacion"],
    )


@router.get("/rutas")
def listar_rutas():
    return RUTAS


@router.get("/rutas/{ruta_id}/tiempos")
def tiempos_estacion_a_estacion(ruta_id: str, velocidad_kmh: float = 28.0):
    """
    Devuelve, para TODA la ruta, el tiempo estimado de viaje de cada
    estación a la siguiente (no requiere un bus en movimiento: es el
    cálculo teórico del corredor completo, útil para mostrar la tabla
    de tiempos en el frontend).
    """
    if ruta_id not in RUTAS:
        raise HTTPException(404, "Ruta no encontrada")

    puntos = RUTAS[ruta_id]
    hora_actual = datetime.now().hour
    factor = factor_hora_pico(hora_actual)

    tramos = []
    tiempo_acumulado_min = 0.0

    for i in range(len(puntos) - 1):
        origen, destino = puntos[i], puntos[i + 1]
        distancia_km = haversine_km(origen["lat"], origen["lng"], destino["lat"], destino["lng"])
        tiempo_min = round((distancia_km / velocidad_kmh) * 60 * factor, 1)
        tiempo_acumulado_min += tiempo_min

        tramos.append({
            "origen": origen["nombre"],
            "destino": destino["nombre"],
            "distancia_km": round(distancia_km, 2),
            "tiempo_estimado_min": tiempo_min,
            "tiempo_acumulado_min": round(tiempo_acumulado_min, 1),
        })

    return {
        "ruta_id": ruta_id,
        "velocidad_asumida_kmh": velocidad_kmh,
        "hora_pico_aplicada": factor > 1.0,
        "tiempo_total_min": round(tiempo_acumulado_min, 1),
        "tramos": tramos,
    }


@router.get("/buses/live", response_model=List[BusPosition])
def buses_en_vivo():
    return [posicion_actual(bus_id) for bus_id in BUSES_ESTADO]


@router.get("/buses/{bus_id}", response_model=BusPosition)
def bus_individual(bus_id: str):
    return posicion_actual(bus_id)


@router.get("/buses/{bus_id}/eta/{stop_index}")
def calcular_eta(bus_id: str, stop_index: int):
    """ETA del bus a una parada específica de su ruta (índice en la lista RUTAS)."""
    pos = posicion_actual(bus_id)
    ruta = RUTAS[pos.ruta_id]

    if stop_index >= len(ruta) or stop_index < pos.siguiente_parada_index - 1:
        raise HTTPException(400, "Índice de parada inválido o ya pasado")

    # Distancia acumulada desde la posición actual hasta la parada destino,
    # sumando los tramos intermedios de la ruta (más realista que línea recta).
    distancia_km = haversine_km(
        pos.lat, pos.lng,
        ruta[pos.siguiente_parada_index]["lat"], ruta[pos.siguiente_parada_index]["lng"],
    )
    for j in range(pos.siguiente_parada_index, stop_index):
        distancia_km += haversine_km(
            ruta[j]["lat"], ruta[j]["lng"],
            ruta[j + 1]["lat"], ruta[j + 1]["lng"],
        )

    hora_actual = datetime.now().hour
    tiempo_horas = (distancia_km / pos.velocidad_kmh) * factor_hora_pico(hora_actual)
    eta_minutos = round(tiempo_horas * 60, 1)

    return {
        "bus_id": bus_id,
        "parada_destino": ruta[stop_index]["nombre"],
        "distancia_km": round(distancia_km, 2),
        "eta_minutos": eta_minutos,
        "hora_consulta": datetime.now().strftime("%H:%M:%S"),
    }
