import cv2
from ultralytics import YOLO
import datetime
import os
import time
import requests

# ==============================================================================
# 1. FUNCIÓN DE CONEXIÓN CON EL MAPA (Tu interfaz con el compañero de geolocalización)
# ==============================================================================
def notificar_incidente_al_mapa(tipo_incidente, latitud, longitud):
    """
    Estructura el incidente en formato JSON y lo envía al sistema del mapa.
    Mientras tu compañero monta el servidor, la función simulará el despacho en consola.
    """
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Este es el paquete de datos estándar (JSON) que tu compañero necesita leer
    datos_incidente = {
        "tipo": tipo_incidente,
        "latitud": latitud,
        "longitud": longitud,
        "fecha_hora": ahora,
        "estado": "Activo",
        "severidad": "Alta"
    }
    
    print(f"\n📡 [EMISOR] Enviando alerta a Geolocalización...")
    print(f"📍 Coordenadas despachadas: [{latitud}, {longitud}] | Incidente: {tipo_incidente.upper()}")
    
    # === UNIÓN FUTURA CON EL MAPA ===
    # Cuando tu compañero tenga su servidor corriendo, solo descomenten las líneas de abajo:
    # try:
    #     url_mapa = "http://localhost:5000/api/incidentes" # URL del servidor de tu compañero
    #     response = requests.post(url_mapa, json=datos_incidente, timeout=3)
    #     print(f"✅ Notificación entregada al mapa con éxito. Código: {response.status_code}")
    # except Exception as e:
    #     print("⚠️ El mapa está desconectado temporalmente. Alerta retenida en caché local.")

# ==============================================================================
# 2. PREPARACIÓN DEL ENTORNO LOCAL
# ==============================================================================
if not os.path.exists("evidencias"):
    os.makedirs("evidencias")

print("Cargando motores de IA...")
modelo_armas = YOLO("yolov8n.pt") 

cap = cv2.VideoCapture(0) 

# Variables de control de flujo
ultimo_tiempo_alerta = 0
intervalo_alertas = 5  # Espera 5 segundos para no duplicar el mismo incidente en el mapa

# Coordenadas fijas de simulación para la vía monitoreada (Ej: Sector Metropolitano / Piedecuesta)
LATITUD_CAMARA = 6.9876
LONGITUD_CAMARA = -73.0498

print("Sistema Orion - Monitoreo de Incidentes y Enlace de Mapa Activo...")

# ==============================================================================
# 3. BUCLE PRINCIPAL DE PROCESAMIENTO
# ==============================================================================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_limpio = frame.copy()
    resultados_armas = modelo_armas(frame, verbose=False)[0]
    arma_detectada = False
    objeto_nombre = ""

    # Análisis de objetos detectados en la vía
    for box in resultados_armas.boxes:
        cls_id = int(box.cls[0])
        label = resultados_armas.names[cls_id]
        confidence = float(box.conf[0])

        # Simulación de incidentes usando objetos comunes (celular, tijeras, cuchillo)
        if label in ["cell phone", "scissors", "knife"] and confidence > 0.4:
            arma_detectada = True
            objeto_nombre = label
            
            # Dibujar caja de detección en caliente
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"PELIGRO: {label}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # LÓGICA DE RESPUESTA A INCIDENTES Y GEOLOCALIZACIÓN
    if arma_detectada:
        tiempo_actual = time.time()
        
        if tiempo_actual - ultimo_tiempo_alerta > intervalo_alertas:
            ahora = datetime.datetime.now()
            fecha_hora_str = ahora.strftime("%Y-%m-%d_%H-%M-%S")
            
            # 1. Almacenamiento local de evidencia física
            nombre_foto = f"evidencias/INCIDENTE_{fecha_hora_str}.jpg"
            cv2.imwrite(nombre_foto, frame_limpio)
            
            # 2. Generación del reporte de auditoría local (Log)
            log_linea = f"[{ahora.strftime('%Y-%m-%d %H:%M:%S')}] ALERTA - Peligro detectado: '{objeto_nombre}'. Foto: {nombre_foto}\n"
            with open("registro_incidentes.txt", "a", encoding="utf-8") as archivo_log:
                archivo_log.write(log_linea)
            
            print(f"\n🔥 ¡INCIDENTE DETECTADO LOCALMENTE! -> {log_linea.strip()}")
            
            # 3. ACTIVAR GEOLOCALIZACIÓN: Despachar el incidente al mapa de tu compañero
            notificar_incidente_al_mapa(objeto_nombre, LATITUD_CAMARA, LONGITUD_CAMARA)
            
            ultimo_tiempo_alerta = tiempo_actual

        # Interfaz de alerta visual en el monitor
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 255), -1)
        cv2.putText(frame, "AMENAZA DE SEGURIDAD EN CURSO - REPORTANDO", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Desplegar pantalla
    cv2.imshow("Sistema Orion - Analizador de Incidentes", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Sistema Orion desconectado.")