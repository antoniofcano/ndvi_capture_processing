import os
import time
import json
import queue
import signal
import threading
import sys
import busio
import board
import adafruit_tsl2591
from concurrent.futures import ThreadPoolExecutor
from picamera2 import Picamera2
from libcamera import controls
import cv2
import io
import numpy as np

class Camera:
    """
    A class that captures images using a camera when a specific light sequence is detected.
    """

    def __init__(self, config_path):
        """
        Initializes the LightTriggeredCamera with a given configuration file path.

        :param config_path: str, path to the JSON configuration file
        """
        self.config_path = config_path
        self.config = self.read_config

        self.camera = self.setup_camera
        self.output_path = self.config['output_path']
        self.capture_config = self.camera.create_still_configuration(raw={})

        self.sensor = self.setup_light_sensor
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.image_queue = queue.Queue(maxsize=self.config['max_queue_size'])
        self.shutdown_event = threading.Event()

    @property
    def read_config(self):
        """
        Reads the camera configuration from a JSON file.

        :param file_path: str, path to the JSON configuration file
        :return: dict, configuration dictionary
        """
        with open(self.config_path) as f:
            config = json.load(f)
        return config

    @property
    def setup_camera(self):
        """
        Configures the camera according to the settings from the configuration file.

        :return: Picamera2, configured camera instance
        """
        camera = Picamera2()

        config = self.config
        camera.sensor_mode = config['sensor_mode']
        camera.resolution = (config['width'], config['height'])
        camera.iso = config['iso']
        camera.framerate = config['framerate']
        camera.exposure_mode = config['exposure_mode']
        camera.awb_mode = config['awb_mode']
        camera.awb_gains = (config['awb_gain_red'], config['awb_gain_blue'])
        camera.image_effect = config['image_effect']
        camera.color_effects = config['color_effects']
        camera.contrast = config['contrast']
        camera.brightness = config['brightness']
        camera.sharpness = config['sharpness']
        camera.saturation = config['saturation']
        camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0})

        return camera

    @property
    def setup_light_sensor(self):
        """
        Configures the light sensor.

        :return: adafruit_tsl2591.TSL2591, configured light sensor instance
        """
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_tsl2591.TSL2591(i2c)
        sensor.gain = adafruit_tsl2591.GAIN_LOW
        return sensor

    def get_next_sequence_number(self):
        """
        Retrieves the next sequence number for the image filenames.

        :return: int, next sequence number
        """
        max_sequence_num = 0
        for filename in os.listdir(self.output_path):
            if filename.startswith('image_'):
                sequence_num = int(filename[6:-4])
                if sequence_num > max_sequence_num:
                    max_sequence_num = sequence_num
        return max_sequence_num + 1

    def save_image(self):
        """
        Saves images from the image_queue to the output directory.
        """
        while True:
            image_buffer, metadata, ext = self.image_queue.get()
            if image_buffer is None:
                break

            filename = os.path.join(self.output_path, 'image_%04d' % self.get_next_sequence_number()) + ext
            if ext == ".jpg":
                self.camera.helpers.save(self.camera.helpers.make_image(image_buffer, self.capture_config["main"]), metadata, filename)
            elif ext == ".dng":
                self.camera.helpers.save_dng(image_buffer, metadata, self.capture_config["raw"], filename)

            self.image_queue.task_done()

    def capture_image(self):
        """
        Captures and enqueues images to be saved.
        """
        buffers, metadata = self.camera.switch_mode_and_capture_buffers(self.capture_config, ["main", "raw"])
        raw_image = buffers[1]
        main_image = buffers[0]

        self.image_queue.put((buffers[0], metadata, ".jpg"))
        self.image_queue.put((raw_image, metadata, ".dng"))

    def get_frame(self):
        #image_buffer, metadata = self.camera.switch_mode_and_capture_buffers(self.capture_config, ["main"])
        #image_buffer = self.camera.capture_array("main")
        #main_image = self.camera.helpers.make_image(image_buffer[0], self.capture_config["main"])

        main_image = self.camera.capture_image()
        main_image_cv2 = np.array(main_image)

        ret, jpeg = cv2.imencode('.jpg', main_image_cv2)
        return jpeg.tobytes()

    def shutdown(self):
        """
        Termina el proceso de captura y guardado de imágenes de manera ordenada.
        
        Esta función coloca un elemento especial en la cola de imágenes, indicando
        que no hay más imágenes para guardar. Luego, espera a que el executor finalice
        y establece el evento de cierre.
        """
        self.image_queue.put((None, None, None))
        self.executor.shutdown(wait=True)
        self.shutdown_event.set()

    def init_pool(self):
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self.save_image)


    def preview_capture(self):
        self.init_pool()
        self.capture_image()
        time.sleep(0.1)

    def light_trigger_capture(self):
        """
        Loop that detects the light sequence and captures images accordingly.
        """
        threshold_on = 3500
        threshold_off = 15
        led_on = True
        led_off = False
        sequence_counter = 0

        self.init_pool()

        try:
            while not self.shutdown_event.is_set():
                lux = self.sensor.lux

                if lux < threshold_off and led_on:
                    led_off = True
                    led_on = False

                elif lux > threshold_on and led_off:
                    led_on = True
                    led_off = False
                    sequence_counter += 1
                    print(f"{sequence_counter} Light sequence detected: off-on-off-on")

                    self.capture_image()

                time.sleep(0.1)

        except KeyboardInterrupt:
            self.shutdown()

