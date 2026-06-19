"""
routes.py - Endpoints de la API (separados del arranque de la app).
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from data import BUSES_ESTADO, RUTAS
from geo import factor_hora_pico, haversine_km, interpolar
from incidents import (
    Incidente,
    IncidenteCrear,
    crear_incidente,
    listar_incidentes,
    resolver_incidente,
)
from models import BusPosition, OcupacionActualizar
from services.occupancy_service import actualizar_ocupacion

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


# ---------------------------------------------------------------------------
# OCUPACIÓN REAL (puente para cámara / YOLO)
# ---------------------------------------------------------------------------
@router.post("/buses/{bus_id}/ocupacion", response_model=BusPosition)
def actualizar_ocupacion_bus(bus_id: str, datos: OcupacionActualizar):
    """
    Endpoint que llama tu pipeline de cámara/YOLO (o cualquier sensor)
    para reportar la ocupación real de un bus. Acepta:
      - {"ocupacion": "lleno"}        -> ya clasificado por ti
      - {"conteo_personas": 27}       -> el backend lo clasifica

    Ver services/occupancy_service.py para los umbrales de clasificación
    y services/yolo_service.py para cómo conectar una cámara real.
    """
    try:
        actualizar_ocupacion(bus_id, ocupacion=datos.ocupacion, conteo_personas=datos.conteo_personas)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    return posicion_actual(bus_id)


# ---------------------------------------------------------------------------
# INCIDENTES VIALES
# ---------------------------------------------------------------------------
@router.get("/incidentes", response_model=List[Incidente])
def obtener_incidentes(solo_activos: bool = True):
    """Lista los incidentes reportados (por defecto, solo los activos)."""
    return listar_incidentes(solo_activos=solo_activos)


@router.post("/incidentes", response_model=Incidente)
def reportar_incidente(datos: IncidenteCrear):
    """
    Reporta un incidente (accidente, trancón, daño de vía, control policial)
    sobre un tramo de la ruta. Mientras esté activo, los buses que pasan
    por ese tramo reducen su velocidad real según la gravedad reportada.
    """
    if datos.ruta_id not in RUTAS:
        raise HTTPException(404, "Ruta no encontrada")

    ruta = RUTAS[datos.ruta_id]
    if not (0 <= datos.segmento_index < len(ruta) - 1):
        raise HTTPException(400, "Índice de tramo inválido para esta ruta")

    if datos.tipo not in {"accidente", "trancon", "danio_via", "control_policial", "otro"}:
        raise HTTPException(400, "Tipo de incidente inválido")
    if datos.gravedad not in {"leve", "moderado", "grave"}:
        raise HTTPException(400, "Gravedad inválida (usa leve | moderado | grave)")

    p1, p2 = ruta[datos.segmento_index], ruta[datos.segmento_index + 1]
    punto_medio = interpolar(p1, p2, 0.5)

    return crear_incidente(datos, punto_medio)


@router.delete("/incidentes/{incidente_id}", response_model=Incidente)
def cerrar_incidente(incidente_id: str):
    """Marca un incidente como resuelto (ya no afecta la velocidad de los buses)."""
    incidente = resolver_incidente(incidente_id)
    if not incidente:
        raise HTTPException(404, "Incidente no encontrado")
    return incidente
