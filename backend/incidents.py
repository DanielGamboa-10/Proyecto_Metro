"""
incidents.py - Incidentes viales reportados sobre el corredor.

Un incidente vive "sobre" un tramo de una ruta (entre la estación
`segmento_index` y la siguiente). Mientras esté activo:
  - se muestra en el mapa
  - los buses que circulan por ese tramo reducen su velocidad real,
    según la gravedad (leve / moderado / grave)

No usamos base de datos todavía: se guarda en memoria (dict). Si luego
quieres persistencia, esta es la única pieza que tocarías (cambiar
INCIDENTES por consultas a una tabla real, p.ej. con SQLModel + SQLite).
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Tipos y gravedad permitidos (úsalos también en el frontend para el selector)
# ---------------------------------------------------------------------------
TIPOS_VALIDOS = {"accidente", "trancon", "danio_via", "control_policial", "otro"}
GRAVEDADES_VALIDAS = {"leve", "moderado", "grave"}

# Cuánto se reduce la velocidad real del bus al pasar por un tramo con
# incidente activo, según su gravedad (1.0 = no afecta, 0.4 = va muy lento)
FACTOR_VELOCIDAD_POR_GRAVEDAD = {
    "leve": 0.9,
    "moderado": 0.65,
    "grave": 0.35,
}


class IncidenteCrear(BaseModel):
    """Lo que manda el cliente (app, formulario web, etc.) al reportar."""
    ruta_id: str
    segmento_index: int          # tramo afectado: entre estación[i] y estación[i+1]
    tipo: str
    gravedad: str
    descripcion: Optional[str] = None
    lat: Optional[float] = None  # si no se manda, se ubica en el punto medio del tramo
    lng: Optional[float] = None


class Incidente(BaseModel):
    """Lo que se guarda y se devuelve al cliente."""
    id: str
    ruta_id: str
    segmento_index: int
    tipo: str
    gravedad: str
    descripcion: Optional[str] = None
    lat: float
    lng: float
    reportado_en: str
    activo: bool = True


# Estado en memoria: id -> Incidente
INCIDENTES: Dict[str, Incidente] = {}


def crear_incidente(datos: IncidenteCrear, punto_medio: dict) -> Incidente:
    incidente_id = uuid.uuid4().hex[:8]
    incidente = Incidente(
        id=incidente_id,
        ruta_id=datos.ruta_id,
        segmento_index=datos.segmento_index,
        tipo=datos.tipo,
        gravedad=datos.gravedad,
        descripcion=datos.descripcion,
        lat=datos.lat if datos.lat is not None else punto_medio["lat"],
        lng=datos.lng if datos.lng is not None else punto_medio["lng"],
        reportado_en=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        activo=True,
    )
    INCIDENTES[incidente_id] = incidente
    return incidente


def listar_incidentes(solo_activos: bool = True) -> List[Incidente]:
    valores = list(INCIDENTES.values())
    if solo_activos:
        valores = [i for i in valores if i.activo]
    return valores


def resolver_incidente(incidente_id: str) -> Optional[Incidente]:
    incidente = INCIDENTES.get(incidente_id)
    if incidente:
        incidente.activo = False
    return incidente


def factor_velocidad_para(ruta_id: str, segmento_index: int) -> float:
    """
    Combina la gravedad de todos los incidentes activos sobre ese tramo
    exacto (puede haber más de uno) y devuelve el multiplicador de
    velocidad más restrictivo (el más lento manda).
    """
    factor = 1.0
    for incidente in INCIDENTES.values():
        if (
            incidente.activo
            and incidente.ruta_id == ruta_id
            and incidente.segmento_index == segmento_index
        ):
            factor = min(factor, FACTOR_VELOCIDAD_POR_GRAVEDAD.get(incidente.gravedad, 1.0))
    return factor
