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

import logging

def handle_signal(signum, frame):
    # Realiza las tareas de limpieza necesarias aquí, si las hay
    # Mapa de señales a mensajes de motivo
    reason_map = {
        signal.SIGTERM: "Se recibió SIGTERM. Limpiando y terminando el programa.",
        signal.SIGINT: "Se recibió SIGINT. Interrupción por el usuario, finalizando.",
        signal.SIGHUP: "Se recibió SIGHUP. Terminal cerrado, finalizando."
    }
    # Obtén el motivo del cierre basado en la señal recibida
    reason = reason_map.get(signum, f"Señal desconocida recibida ({signum}). Limpiando y terminando el programa.")
    logging.info(reason)

    # Cerrar la cámara
    camera.close()

    #Libera el bus i2c
    i2c.deinit()

    # Detén el proceso de guardado cuando se interrumpa la captura
    try:
        image_queue.put((None, None, None))
        image_queue.join()
    Exception:
        logging.info(f"image_queue not defined: {e}")

    # Finalizar todos los hilos
    executor.shutdown(wait=True)

    sys.exit(0)

def get_last_sequence_number(output_path):
    max_sequence_num = 0
    for filename in os.listdir(output_path):
        if filename.startswith('image_'):
            sequence_num = int(filename[6:-4])
            if sequence_num > max_sequence_num:
                max_sequence_num = sequence_num
    return max_sequence_num

def read_config(file_path):
    try:
        with open(file_path) as f:
            config = json.load(f)
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.exception(f"Error al leer el archivo de configuración: {e}")
        sys.exit(1)
def setup_camera(config):
    try:
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
    except Exception as e:
        logging.exception(f"Error al configurar la cámara: {e}")
        sys.exit(1)

def save_image(image_queue, capture_config):

    try:
        while True:
            image_buffer, metadata, ext, filename = image_queue.get()
            if image_buffer is None:
                break

            if ext == ".jpg":
                camera.helpers.save(camera.helpers.make_image(image_buffer, capture_config["main"]), metadata, filename)
            elif ext == ".dng":
                camera.helpers.save_dng(image_buffer, metadata, capture_config["raw"], filename)

            # Indica que la tarea se ha completado
            image_queue.task_done()
    except Exception as e:
        logging.exception(f"Error al guardar la imagen: {e}")
        image_queue.task_done()
        
def capture_image(camera, capture_config, output_path):
    try:
        buffers, metadata = camera.switch_mode_and_capture_buffers(capture_config, ["main", "raw"])
        raw_image = buffers[1]
        main_image = buffers[0]

        # Espera si la cola está llena
        image_queue.put((main_image, metadata, ".jpg"))
        image_queue.put((raw_image, metadata, ".dng"))

        # Espera si la cola está llena
        sequence_counter += 1
        filename = os.path.join(output_path, 'image_%04d' % sequence_counter)
        image_queue.put((main_image, metadata, ".jpg", filename))
        image_queue.put((raw_image, metadata, ".dng", filename))

    except Exception as e:
        logging.exception(f"Error al capturar la imagen: {e}")


# Lee la configuración desde un archivo JSON
config = read_config('config.json')
# Inicializa las variables desde la configuración
threshold_on = config.get('threshold_on', 3500)
threshold_off = config.get('threshold_off', 15)
max_pool_threads = config.get('max_pool_threads', 1)
max_queue_size = config.get('max_queue_size', 5)
sensor_read_delay = config.get('sensor_read_delay', 0.1)
log_level = config.get('log_level', 'INFO')
log_file = config.get('log_file', 'app.log')
output_path = config['output_path']

# Configura el nivel de log a INFO, de modo que se registrarán todos los mensajes de nivel INFO y superior
# También configura el formato del mensaje de log y especifica que los mensajes de log deben guardarse en un archivo llamado 'app.log'
logging.basicConfig(filename=log_file, level=getattr(logging, log_level.upper()), format='%(asctime)s - %(levelname)s - %(message)s')

# Inicializa el contador de secuencia al arrancar el script
sequence_counter = get_last_sequence_number(output_path)

# Crea un manejador de log para la salida estándar y añádelo al logger raíz
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


# Registra el controlador de la señal SIGTERM (kill) y SIGINT (Ctrl-C)
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

try:
    # Configura la conexión I2C
    i2c = busio.I2C(board.SCL, board.SDA)

    # Crea una instancia del sensor TSL2591
    sensor = adafruit_tsl2591.TSL2591(i2c)
    sensor.gain = adafruit_tsl2591.GAIN_LOW
except Exception as e:
    logging.exception(f"Error al inicializar el sensor de luz: {e}")
    sys.exit(1)

#Inicializa la Camara
contador = 0
camera = setup_camera(config)
capture_config = camera.create_still_configuration(raw={})

try:
    camera.start()
    time.sleep(2)
except Exception as e:
    logging.exception(f"Error al iniciar la cámara: {e}")
    sys.exit(1)

#Inicializa el entorno MultiThread
# Crea un ThreadPoolExecutor con 1 hilo
executor = ThreadPoolExecutor(max_workers=max_pool_threads)

# Crea una cola con un límite máximo de elementos
image_queue = queue.Queue(maxsize=max_queue_size)

# Inicia max_pool_threads hilos para guardar imágenes desde la cola
for _ in range(max_pool_threads):
    executor.submit(save_image, image_queue, capture_config)

LED_OFF = 0
LED_ON = 1

# Estado inicial del LED
led_state = LED_OFF
try:
    while True:
        # Lee el valor de lux del sensor
        lux = sensor.lux

        # Comprueba si el LED se ha apagado (lux < threshold_off) y estaba previamente encendido
        if lux < threshold_off and led_state == LED_ON:
            led_state = LED_OFF

        # Si la secuencia de apagado-encendido se ha completado
        # Comprueba si el LED se ha encendido (lux > threshold_on) y estaba previamente apagado
        elif lux > threshold_on and led_state == LED_OFF:
            led_state = LED_ON
            contador = contador + 1
            logging.debug(f"{contador} Secuencia encendido-apagado-encendido detectada!")

            # Captura la imagen
            capture_image(camera, capture_config, output_path)

        # Espera antes de leer el siguiente valor
        time.sleep(sensor_read_delay)
except KeyboardInterrupt:
    logging.info("Interrupción por el usuario, finalizando...")
except Exception as e:
    logging.exception(f"Error inesperado durante la captura de imágenes: {e}")
finally:
    sys.exit(0)