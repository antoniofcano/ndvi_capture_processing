import time
import board
import busio
import adafruit_tsl2591

# Configura la conexión I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Crea una instancia del sensor TSL2591
sensor = adafruit_tsl2591.TSL2591(i2c)
# Configura la ganancia del sensor
sensor.gain = adafruit_tsl2591.GAIN_LOW

# Umbral para determinar si el LED está encendido o apagado
threshold_on = 3500
threshold_off = 15

# Estado del LED
led_on = True
led_off = False

contador = 0
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
        print("%d Secuencia encendido-apagado-encendido detectada!", contador)

    # Espera 100 ms antes de leer el siguiente valor
    time.sleep(0.1)
