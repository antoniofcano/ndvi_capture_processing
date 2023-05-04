#!/usr/bin/env python3

import time
import board
import busio
import adafruit_tsl2591

from picamera2 import Picamera2
from libcamera import controls
import json

import os.path
import signal
import sys

import os
import queue
from concurrent.futures import ThreadPoolExecutor


def sigterm_handler(signal, frame):
    # Realiza las tareas de limpieza necesarias aquí, si las hay
    print("Terminando el servicio...")
    sys.exit(0)


def get_next_sequence_number(output_path):
    max_sequence_num = 0
    for filename in os.listdir(output_path):
        if filename.startswith('image_'):
            sequence_num = int(filename[6:-4])
            if sequence_num > max_sequence_num:
                max_sequence_num = sequence_num
    return max_sequence_num + 1

def read_config(file_path):
    with open(file_path) as f:
        config = json.load(f)
    return config

def setup_camera(config):
    camera = Picamera2()
    camera.sensor_mode = config['sensor_mode']
    camera.resolution = (config['width'], config['height'])
    camera.iso = config['iso']
    camera.framerate = config['framerate']
    camera.exposure_mode = config['exposure_mode']
    #White Balance settings
    camera.awb_mode = config['awb_mode']
    camera.awb_gains = ( config['awb_gain_red'], config['awb_gain_blue'])

    camera.image_effect = config['image_effect']
    camera.color_effects = config['color_effects']
    camera.contrast = config['contrast']
    camera.brightness = config['brightness']
    camera.sharpness = config['sharpness']
    camera.saturation = config['saturation']

    #Manual Focus infinite
    camera.set_controls( {"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0} )
    return camera

def save_image(image_queue, output_path, capture_config):
    while True:
        image_buffer, metadata, ext = image_queue.get()
        if image_buffer is None:
            break

        filename = os.path.join(output_path, 'image_%04d' % get_next_sequence_number(output_path)) + ext
        if ext == ".jpg":
            camera.helpers.save(camera.helpers.make_image(image_buffer, capture_config["main"]), metadata, filename)
        elif ext == ".dng":
            camera.helpers.save_dng(image_buffer, metadata, capture_config["raw"], filename)

        # Indica que la tarea se ha completado
        image_queue.task_done()


#def capture_image(camera, capture_config, output_path):
#    filename = os.path.join(output_path, 'image_%04d' % get_next_sequence_number(output_path))
    #camera.start_and_capture_file(filename)

#    buffers, metadata = camera.switch_mode_and_capture_buffers(capture_config, ["main", "raw"])
#    raw_image = buffers[1]

#    camera.helpers.save(camera.helpers.make_image(buffers[0], capture_config["main"]), metadata, filename + ".jpg")
#    camera.helpers.save_dng(raw_image, metadata, capture_config["raw"], filename + ".dng")

def capture_image(camera, capture_config, output_path):
    buffers, metadata = camera.switch_mode_and_capture_buffers(capture_config, ["main", "raw"])
    raw_image = buffers[1]
    main_image = buffers[0]

    # Espera si la cola está llena
    image_queue.put((buffers[0], metadata, ".jpg"))
    image_queue.put((raw_image, metadata, ".dng"))


# Registra el controlador de la señal SIGTERM
signal.signal(signal.SIGTERM, sigterm_handler)

# Lee la configuración desde un archivo JSON
config = read_config('config.json')

# Configura la conexión I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Crea una instancia del sensor TSL2591
sensor = adafruit_tsl2591.TSL2591(i2c)
sensor.gain = adafruit_tsl2591.GAIN_LOW

# Umbral para determinar si el LED está encendido o apagado
threshold_on = 3500
threshold_off = 15

# Estado del LED
led_on = True
led_off = False

#Inicializa la Camara
contador = 0
camera = setup_camera(config)
capture_config = camera.create_still_configuration(raw={})
output_path = config['output_path']

camera.start()
time.sleep(2)

#Inicializa el entorno MultiThread
# Crea un ThreadPoolExecutor con 1 hilo
executor = ThreadPoolExecutor(max_workers=1)

# Crea una cola con un límite máximo de elementos
max_queue_size = 5
image_queue = queue.Queue(maxsize=max_queue_size)

# Inicia un hilo para guardar imágenes desde la cola
executor.submit(save_image, image_queue, output_path, capture_config)


try:
    while True:
        # Lee el valor de lux del sensor
        lux = sensor.lux

        # Verifica si el LED está apagado (lux < threshold_off) y si estaba previamente encendido
        if lux < threshold_off and led_on:
            led_off = True
            led_on = False

        # Si se cumplió la secuencia apagado-encendido
        # Verifica si el LED está encendido (lux > threshold_on) y si estaba previamente apagado
        elif lux > threshold_on and led_off:
            led_on = True
            led_off = False
            contador = contador + 1
            print(f"{contador} Secuencia encendido-apagado-encendido detectada!")

            # Captura la imagen
            capture_image(camera, capture_config, output_path)

        # Espera 100 ms antes de leer el siguiente valor
        time.sleep(0.1)
except KeyboardInterrupt:
        # Detén el proceso de guardado cuando se interrumpa la captura
        image_queue.put((None, None, None))
        image_queue.join()
        executor.shutdown(wait=True)
