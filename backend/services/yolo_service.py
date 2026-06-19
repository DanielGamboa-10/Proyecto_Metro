"""
services/yolo_service.py - Plantilla para conectar conteo de pasajeros
con un modelo de visión (YOLO) sobre video de cámara dentro del bus.

Este archivo es una PLANTILLA. No trae un modelo entrenado ni acceso a
cámara real (eso depende de tu hardware/infra). Lo que sí define es el
CONTRATO: una función que recibe un frame y devuelve un conteo de
personas, para que el resto del backend (occupancy_service, routes)
no tenga que saber nada de YOLO.

---------------------------------------------------------------------
CÓMO CONECTAR UN MODELO YOLO REAL (ej. con la librería `ultralytics`):

    pip install ultralytics opencv-python

    from ultralytics import YOLO
    modelo = YOLO("yolov8n.pt")  # modelo pequeño, rápido; clase 0 = "person"

    def contar_personas_en_frame(frame) -> int:
        resultados = modelo(frame, classes=[0], verbose=False)  # solo personas
        return len(resultados[0].boxes)

---------------------------------------------------------------------
CÓMO LEER UNA CÁMARA EN VIVO Y EMPUJAR EL DATO AL BACKEND:

    import cv2
    import requests

    captura = cv2.VideoCapture(0)  # 0 = primera cámara; o RTSP/URL de la cámara del bus
    while True:
        ok, frame = captura.read()
        if not ok:
            continue
        conteo = contar_personas_en_frame(frame)
        requests.post(
            "http://localhost:8000/buses/bus_01/ocupacion",
            json={"conteo_personas": conteo},
            timeout=3,
        )
        # espera unos segundos antes del siguiente frame para no saturar
"""

import random


def contar_personas_en_frame(frame) -> int:
    """
    Punto de entrada real: reemplaza el cuerpo de esta función por tu
    inferencia YOLO (ver comentario arriba). `frame` sería una imagen
    (numpy array de OpenCV, por ejemplo).
    """
    raise NotImplementedError(
        "Conecta aquí tu modelo YOLO real. Ver las instrucciones en el "
        "encabezado de este archivo."
    )


def simular_conteo_personas() -> int:
    """
    Generador de conteo FALSO, solo para demos sin cámara real.
    Úsalo para probar el flujo completo (POST /buses/{id}/ocupacion)
    antes de tener hardware de cámara conectado.
    """
    return random.randint(0, 45)
