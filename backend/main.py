"""
main.py - Backend - Geolocalización simulada de buses + ETA
Hackathon Metrolínea - Bucaramanga

Estructura (cada cosa en su archivo):
    data.py       -> rutas y estado inicial de los buses
    models.py     -> modelos Pydantic
    geo.py        -> matemáticas (distancia, interpolación, hora pico)
    simulator.py  -> tarea de fondo que mueve los buses
    routes.py     -> endpoints de la API
    main.py       -> arma todo y levanta el servidor (este archivo)

Instalación:
    pip install fastapi uvicorn

Ejecutar (desde la carpeta backend/):
    uvicorn main:app --reload --port 8000

Endpoints:
    GET  /buses/live                       -> posición actual de todos los buses
    GET  /buses/{bus_id}                   -> posición de un bus específico
    GET  /buses/{bus_id}/eta/{stop_index}   -> ETA del bus a una parada de su ruta
    GET  /rutas                            -> rutas disponibles con sus paradas
    GET  /rutas/{ruta_id}/tiempos          -> tiempos estimados estación a estación
"""

import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import router
from simulator import mover_buses

app = FastAPI(title="Metrolínea Live - Geolocalización")

# Se mantiene por si en algún momento separas frontend y backend de nuevo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Primero las rutas de la API (para que /rutas, /buses/... respondan JSON)
app.include_router(router)


@app.on_event("startup")
async def iniciar_simulacion():
    asyncio.create_task(mover_buses())


# ---------------------------------------------------------------------------
# Frontend: se sirve desde el mismo servidor.
# Estructura real del proyecto:
#   Proyecto_Metro/
#     index.html      <- está en la RAÍZ, no dentro de frontend/
#     backend/         <- aquí está este main.py
#     frontend/
#       css/
#       js/
# ---------------------------------------------------------------------------
from fastapi.responses import FileResponse

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
INDEX_HTML = ROOT_DIR / "index.html"


@app.get("/", include_in_schema=False)
def servir_index():
    return FileResponse(INDEX_HTML)


# Sirve todo lo de frontend/ (css, js, assets futuros) bajo /frontend/...
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# Sirve la carpeta assets/ de la raíz, si la usas para imágenes/íconos
ASSETS_DIR = ROOT_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
