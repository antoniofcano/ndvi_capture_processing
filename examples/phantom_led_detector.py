import time
import board
import busio
import adafruit_tsl2591

# Configurar I2C y TSL2591
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_tsl2591.TSL2591(i2c)
# Configura la ganancia del sensor
sensor.gain = adafruit_tsl2591.GAIN_LOW

# Configurar umbrales
RED_LED_LUX_THRESHOLD = 500  # Ajusta este valor según el brillo del LED rojo
LED_BLINK_TIME = 0.5  # Ajusta este valor según la duración del parpadeo del LED (en segundos)

def detect_led_blink():
    led_on = False
    led_blink_detected = False

    while not led_blink_detected:
        lux = sensor.lux
        print("Lux:", lux)

        if lux >= RED_LED_LUX_THRESHOLD and not led_on:
            led_on = True
            led_on_time = time.time()

        if lux < RED_LED_LUX_THRESHOLD and led_on:
            led_off_time = time.time()
            if led_off_time - led_on_time <= LED_BLINK_TIME:
                led_blink_detected = True
            led_on = False

    return led_blink_detected

def main():
    while True:
        if detect_led_blink():
            print("Parpadeo del LED detectado")
            # Aquí puedes agregar el código para capturar una foto o realizar cualquier otra acción
            # Por ejemplo: capture_noir_photo("noir_photo.jpg")
            time.sleep(1)  # Esperar un segundo antes de volver a buscar parpadeos

if __name__ == "__main__":
    main()
