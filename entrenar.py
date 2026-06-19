from ultralytics import YOLO
import os

if __name__ == '__main__':
    # 1. Cargar el modelo base preentrenado
    model = YOLO("yolov8n.pt")

    # 2. Obtener la ruta absoluta del archivo data.yaml
    # Esto asegura que Python encuentre el archivo sin importar las barras de Windows
    ruta_yaml = os.path.abspath("Train-weapon-3/data.yaml")

    # 3. Lanzar el entrenamiento
    # Nota: Si tienes tarjeta gráfica NVIDIA con CUDA configurada, cambia device='cpu' por device=0
    # Dejamos 20 épocas para que no demore una eternidad en el procesador
    model.train(data=ruta_yaml, epochs=20, imgsz=640, device='cpu')