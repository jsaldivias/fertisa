# Agregar R12, R22
import sys
import time
import RPi.GPIO as GPIO
from hx711 import HX711

# Pin definitions
evFinalCarga1 = 27
luzDescarga1 = 13
swAutoManu = 22
evFinalCarga2 = 16

# Pin setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(evFinalCarga1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(luzDescarga1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(swAutoManu, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(evFinalCarga2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# mm2 (BCM23 y BCM24)
hx2 = HX711(dout=23, pd_sck=24)
# mm1 (BCM5 y BCM6)
hx1 = HX711(dout=5, pd_sck=6)

# Calibracion de mm1-mm2
hx2.setReferenceUnit(210)
hx1.setReferenceUnit(210)

# Tara mm1-mm2 al mismo tiempo
hx2.reset()
hx2.tare()

hx1.reset()
hx1.tare()

while True:

    try:
        if evFinalCarga1 == 1:
            val1 = hx1.getWeight()    
            print("{0: 4.4f}".format(val1))
        else:
            if evFinalCarga2 == 1:
                val2 = hx2.getWeight()
                print("{0: 4.4f}".format(val2))
        

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        sys.exit()
