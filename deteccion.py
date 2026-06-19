from ultralytics import YOLO
import cv2
import time

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

FPS = 30
UMBRAL_MERODEO_SEG = 10  # segundos quieto para activar alerta (10 para demo, 60 real)
UMBRAL_MOVIMIENTO_PX = 30  # píxeles que debe moverse para no contar como quieto

# Diccionario para rastrear cada persona por su ID
personas = {}  # {id: {"centro": (x,y), "frames_quieto": 0, "alerta": False}}

def get_centro(box):
    x1, y1, x2, y2 = box
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))

def distancia(p1, p2):
    return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) ** 0.5

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, persist=True, classes=[0])

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.cpu().numpy().astype(int)

        for box, pid in zip(boxes, ids):
            centro = get_centro(box)

            if pid not in personas:
                personas[pid] = {
                    "centro": centro,
                    "frames_quieto": 0,
                    "alerta": False,
                    "tiempo_alerta": None
                }
            else:
                dist = distancia(centro, personas[pid]["centro"])

                if dist < UMBRAL_MOVIMIENTO_PX:
                    personas[pid]["frames_quieto"] += 1
                else:
                    personas[pid]["frames_quieto"] = 0
                    personas[pid]["alerta"] = False

                personas[pid]["centro"] = centro

                segundos_quieto = personas[pid]["frames_quieto"] / FPS

                if segundos_quieto >= UMBRAL_MERODEO_SEG:
                    personas[pid]["alerta"] = True

            # Dibujar bounding box
            x1, y1, x2, y2 = map(int, box)
            color = (0, 0, 255) if personas[pid]["alerta"] else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Etiqueta
            if personas[pid]["alerta"]:
                cv2.putText(frame, f"⚠️ MERODEO ID:{pid}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                seg = int(personas[pid]["frames_quieto"] / FPS)
                cv2.putText(frame, f"ID:{pid} quieto:{seg}s", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Limpiar IDs que ya no están en escena
    ids_actuales = set(results[0].boxes.id.cpu().numpy().astype(int)) if results[0].boxes.id is not None else set()
    personas = {k: v for k, v in personas.items() if k in ids_actuales}

    cv2.imshow("Seguridad Metrolinea - Merodeo", frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()