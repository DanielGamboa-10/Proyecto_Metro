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

# Guardará el historial de las personas: { (x_centro, y_centro): tiempo_inicial }
rastreo_personas = {}
TIEMPO_MERODEO = 10.0  # Límite de tiempo en segundos

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_limpio = frame.copy()
    # Ejecutamos YOLOv8
    resultados_armas = modelo_armas(frame, verbose=False)[0]
    
    amenaza_detectada = False
    merodeo_detectado = False
    objeto_nombre = ""
    
    # Aquí guardaremos los centros de las personas que están en ESTE cuadro actual
    centros_actuales = []
    ahora_tiempo = time.time()

    # Análisis de detecciones
    for box in resultados_armas.boxes:
        cls_id = int(box.cls[0])
        label = resultados_armas.names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # ----------------------------------------------------------------------
        # CASO 1: ARMAS Y CORTOPUNZANTES (Prioridad Máxima / Alerta Inmediata)
        # ----------------------------------------------------------------------
        # Bajamos la confianza a 0.25 para simulación; el modelo base es ciego con objetos pequeños
        threat_labels = ["knife", "scissors", "handgun", "pistol", "weapon"]
        if label in threat_labels and confidence > 0.25:
            amenaza_detectada = True
            objeto_nombre = label
            
            # Caja ROJA e inmediata
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(frame, f"¡AMENAZA: {label.upper()}!", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # ----------------------------------------------------------------------
        # CASO 2: CONTROL DE MERODEO (Rastreo por posición física)
        # ----------------------------------------------------------------------
        elif label == "person" and confidence > 0.4:
            # Calculamos el centro físico de la persona en la pantalla
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            # Buscamos si este centro coincide con alguien que ya veníamos siguiendo
            encontrado = False
            llave_coincidente = None
            
            # Margen de movimiento en píxeles para considerar que es la misma persona
            UMBRAL_MOVIMIENTO = 80 
            
            for (px, py) in rastreo_personas.keys():
                if abs(cx - px) < UMBRAL_MOVIMIENTO and abs(cy - py) < UMBRAL_MOVIMIENTO:
                    encontrado = True
                    llave_coincidente = (px, py)
                    break
            
            if encontrado:
                # Si ya existía, recuperamos su tiempo inicial y actualizamos su posición
                tiempo_inicio = rastreo_personas[llave_coincidente]
                # Reemplazamos la vieja posición por la nueva en la lista de activos
                del rastreo_personas[llave_coincidente]
                rastreo_personas[(cx, cy)] = tiempo_inicio
                centros_actuales.append((cx, cy))
            else:
                # Si es nueva o acaba de volver a entrar, empieza desde 0 segundos
                rastreo_personas[(cx, cy)] = ahora_tiempo
                centros_actuales.append((cx, cy))
            
            # Calcular permanencia
            tiempo_permanencia = ahora_tiempo - rastreo_personas[(cx, cy)]

            if tiempo_permanencia >= TIEMPO_MERODEO:
                merodeo_detectado = True
                objeto_nombre = f"Merodeador"
                # Caja NARANJA de Peligro por tiempo
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                cv2.putText(frame, f"ALERT: Merodeo ({tiempo_permanencia:.1f}s)", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            else:
                # Caja VERDE de Pasajero normal
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                cv2.putText(frame, f"Pasajero ({tiempo_permanencia:.1f}s)", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # LIMPIEZA INMEDIATA: Si un centro no se detectó en este cuadro, se borra.
    # Esto asegura que si sales de la cámara y vuelves, tu tiempo regrese a 0.
    for posicion in list(rastreo_personas.keys()):
        if posicion not in centros_actuales:
            del rastreo_personas[posicion]

    # ----------------------------------------------------------------------
    # SISTEMA DE DISPARO DE ALERTAS
    # ----------------------------------------------------------------------
    if amenaza_detectada or merodeo_detectado:
        tiempo_actual = time.time()
        
        if tiempo_actual - ultimo_tiempo_alerta > intervalo_alertas:
            ahora_fecha = datetime.datetime.now()
            fecha_hora_str = ahora_fecha.strftime("%Y-%m-%d_%H-%M-%S")
            
            # 1. Foto de evidencia
            nombre_foto = f"evidencias/INCIDENTE_{fecha_hora_str}.jpg"
            cv2.imwrite(nombre_foto, frame_limpio)
            
            # 2. Archivo Log
            tipo_alerta = "AMENAZA DIRECTA" if amenaza_detectada else "ALERTA MERODEO"
            log_linea = f"[{ahora_fecha.strftime('%Y-%m-%d %H:%M:%S')}] {tipo_alerta} - '{objeto_nombre}'. Foto: {nombre_foto}\n"
            with open("registro_incidentes.txt", "a", encoding="utf-8") as archivo_log:
                archivo_log.write(log_linea)
            
            print(f"\n🔥 [SISTEMA METRO] -> {log_linea.strip()}")
            
            # 3. Enlace con tu compañero del mapa
            notificar_incidente_al_mapa(objeto_nombre, LATITUD_CAMARA, LONGITUD_CAMARA)
            
            ultimo_tiempo_alerta = tiempo_actual

        # Banner superior en pantalla
        color_banner = (0, 0, 255) if amenaza_detectada else (0, 165, 255)
        texto_banner = "AMENAZA: OBJETO PELIGROSO DETECTADO" if amenaza_detectada else "ADVERTENCIA: USUARIO MERODEANDO"
        
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), color_banner, -1)
        cv2.putText(frame, texto_banner, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Mostrar ventana
    cv2.imshow("Sistema Orion - Analizador de Incidentes", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Sistema Orion desconectado.")