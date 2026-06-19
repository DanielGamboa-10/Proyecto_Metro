from roboflow import Roboflow

# Reemplaza "TU_API_KEY_REAL" con el código largo de números y letras que te dio Roboflow
rf = Roboflow(api_key="Rmki1fTsv8sQP9T3mtuB") 

project = rf.workspace("wd-pigj0").project("train-weapon")
version = project.version(3)
dataset = version.download("yolov8")