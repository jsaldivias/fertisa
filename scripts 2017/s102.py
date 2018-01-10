# Acepta 2 minimates
import sys
import time

import RPi.GPIO as GPIO
from hx711 import HX711

# Minimate2 (BCM23 y BCM24)
hx2 = HX711(dout=23, pd_sck=24)
# Minimate1 (BCM5 y BCM6)
hx1 = HX711(dout=5, pd_sck=6)
# Aqui va la calibracion de cada celda
hx2.setReferenceUnit(210)
hx1.setReferenceUnit(210)
# Se taran ambas minimate al mismo tiempo
hx2.reset()
hx2.tare()

hx1.reset()
hx1.tare()

while True:

    try:
        val1 = hx1.getWeight()
        val2 = hx2.getWeight()
        print("{0: 4.4f}".format(val2))
        print("{0: 4.4f}".format(val1))

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        sys.exit()
