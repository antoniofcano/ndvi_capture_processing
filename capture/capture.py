import json
import os.path
import time
from picamera2 import Picamera2

def get_next_sequence_number(output_path):
    # Encuentra el número de secuencia de la imagen más reciente
    max_sequence_num = 0
    for filename in os.listdir(output_path):
        if filename.startswith('image_'):
            sequence_num = int(filename[6:-4])
            if sequence_num > max_sequence_num:
                max_sequence_num = sequence_num

    # Devuelve el número de secuencia siguiente
    return max_sequence_num + 1

# Lee la configuración desde un archivo JSON
with open('config.json') as f:
    config = json.load(f)

# Configura la cámara con los parámetros del archivo JSON
camera = Picamera2()
camera.sensor_mode = config['sensor_mode']
camera.resolution = (config['width'], config['height'])
camera.framerate = config['framerate']
camera.exposure_mode = config['exposure_mode']
camera.awb_mode = config['awb_mode']
camera.image_effect = config['image_effect']
camera.color_effects = config['color_effects']
camera.contrast = config['contrast']
camera.brightness = config['brightness']
camera.sharpness = config['sharpness']
camera.saturation = config['saturation']

# Espera a que la cámara ajuste el enfoque y la exposición
time.sleep(2)

# Captura la imagen y la guarda en la ruta especificada
filename = os.path.join(config['output_path'], 'image_%04d.jpg' % get_next_sequence_number(config['output_path']))

camera.start_and_capture_file(filename)
