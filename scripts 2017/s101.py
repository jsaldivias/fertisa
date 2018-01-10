import sys
import time

import RPi.GPIO as GPIO
from hx711 import HX711

# Eleccion de nuevos pines (BCM23 y BCM24)
hx = HX711(dout=23, pd_sck=24)

# HOW TO CALCULATE THE REFFERENCE UNIT
#########################################
# To set the reference unit to 1.
# Call get_weight before and after putting 1000g weight on your sensor.
# Divide difference with grams (1000g) and use it as refference unit.

hx.setReferenceUnit(210)

hx.reset()
hx.tare()

while True:

    try:
        val = hx.getWeight()
        print("{0: 4.4f}".format(val))

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        sys.exit()
