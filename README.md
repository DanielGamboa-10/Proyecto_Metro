# 🚍 Metrolínea Live

<div align="center">

Sistema inteligente de monitoreo y geolocalización en tiempo real para el sistema de transporte Metrolínea de Bucaramanga.

Desarrollado para la **Hackathon Metrolínea**, integrando simulación de rutas, estimación de tiempos de llegada y detección de incidentes mediante visión artificial.

</div>

---

## 📋 Descripción

**Metrolínea Live** es una plataforma que permite visualizar la ubicación de los buses en tiempo real, consultar rutas y estaciones, calcular tiempos estimados de llegada (ETA) y detectar incidentes mediante inteligencia artificial.

El sistema está compuesto por un backend desarrollado con **FastAPI**, una interfaz web interactiva y módulos de visión por computador basados en **YOLOv8**.

---

## ✨ Características

- 📍 Seguimiento de buses en tiempo real.
- 🛣️ Consulta de rutas y estaciones.
- ⏱️ Cálculo de tiempos estimados de llegada (ETA).
- 🚦 Simulación dinámica del movimiento de los vehículos.
- 👥 Estimación de ocupación de pasajeros.
- ⚠️ Gestión y detección automática de incidentes.
- 🧠 Integración con modelos de visión artificial mediante YOLOv8.
- 🌐 Interfaz web interactiva.

---

## 🏗 Arquitectura del proyecto

```text
Proyecto_Metro
│
├── backend
│   ├── data.py
│   ├── geo.py
│   ├── incidents.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── simulator.py
│   └── services
│       ├── occupancy_service.py
│       └── yolo_service.py
│
├── frontend
│   ├── css
│   │   └── style.css
│   └── js
│       ├── app.js
│       └── alerts.js
│
├── pagina puntos
│   ├── puntos.html
│   ├── puntos.css
│   └── puntos.js
│
├── detector_incidentes.py
├── deteccion.py
├── entrenar.py
├── descargar_data.py
└── index.html
```

---

## 🛠 Tecnologías utilizadas

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

### Frontend

- HTML5
- CSS3
- JavaScript
- Leaflet.js

### Inteligencia Artificial

- YOLOv8
- OpenCV
- Ultralytics

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/DanielGamboa-10/Proyecto_Metro.git
cd Proyecto_Metro
```

### 2. Crear entorno virtual

#### Windows

```bash
python -m venv env
env\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv env
source env/bin/activate
```

### 3. Instalar dependencias

```bash
pip install fastapi uvicorn ultralytics opencv-python pydantic
```

---

## ▶️ Ejecución

Desde la carpeta `backend`:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

La aplicación estará disponible en:

```text
http://localhost:8000
```

Documentación automática de la API:

```text
http://localhost:8000/docs
```

---

## 📡 Endpoints principales

### Obtener todos los buses

```http
GET /buses/live
```

### Obtener información de un bus

```http
GET /buses/{bus_id}
```

### Consultar ETA de una parada

```http
GET /buses/{bus_id}/eta/{stop_index}
```

### Consultar rutas

```http
GET /rutas
```

### Consultar tiempos entre estaciones

```http
GET /rutas/{ruta_id}/tiempos
```

---

## 🧠 Módulo de detección de incidentes

El sistema incorpora un componente basado en **YOLOv8**, capaz de detectar eventos y generar alertas para mejorar la seguridad y la supervisión del sistema de transporte.

Para ejecutar:

```bash
python detector_incidentes.py
```

---

## 🎯 Objetivo

Proporcionar una solución tecnológica que permita optimizar la operación del sistema Metrolínea mediante:

- Monitoreo en tiempo real.
- Predicción de tiempos de llegada.
- Gestión de incidentes.
- Análisis inteligente mediante visión artificial.

---

## 👨‍💻 Autores

### Daniel Gamboa
### Filip Sanabria
### Sebastian Salas
### kevin Castillo

### Hackathon Metrolínea – Bucaramanga, Colombia

---

## 📄 Licencia

Este proyecto fue desarrollado con fines académicos y de innovación tecnológica.
