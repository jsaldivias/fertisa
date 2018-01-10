# s104.py Publica en MQTT
# 
# 

import paho.mqtt.client as mqtt  #import the client1
import sys
import time
import RPi.GPIO as GPIO
from hx711 import HX711

# MQTT
def on_connect(client, userdata, flags, rc):
    m="BANDERAS "+str(flags)+"  CODIGO CR  "\
    +str(rc)+"  CLIENTE    "+str(client) \
    +"  USER DATA    "+str(userdata)
    print(m)

def on_message(client1, userdata, message):
    print("   PUBLICADO   "  ,str(message.payload.decode("utf-8")))
broker_address="192.168.0.103"
client1 = mqtt.Client("SACKET1")    # Crea nueva instancia
client1.on_connect= on_connect  # Attach function to callback
client1.on_message=on_message   # Attach function to callback

# Pin definitions
evFinalCarga1 = 27
luzDescarga1 = 13
swAutoManu = 22
evFinalCarga2 = 4

# Pin setup
# IN = 1 Cuando recibe 3.3 V
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
# Conecta MQTT
client1.connect(broker_address) # Connect to broker
client1.loop_start()    # Start the loop
client1.subscribe("s1/R12") # Crea topico R12 en Sacket1
client1.subscribe("s1/R22") # Crea topico R22 en Sacket1
client1.subscribe("s1/peso1") # Crea topico p1 en Sacket1

while True:

    try:
        R12 = GPIO.input(evFinalCarga1)
        
        if R12 == 1:
            peso1 = hx1.getWeight()
            print (R12)
            print("{0: 4.4f}".format(peso1))
            strR12=str(R12) # Convierte en string valor leido
            strPeso1=str(peso1)
            client1.publish("s1/R12",strR12) # Publica topico
            client1.publish("s1/peso1",strPeso1) # Publica peso 
            time.sleep(.2)
        R22 = GPIO.input(evFinalCarga2)
        if R22 == 1:
            print(R22)
            peso2 = hx2.getWeight()
            print("{0: 4.4f}".format(peso2))
    except (KeyboardInterrupt, SystemExit):
        client1.disconnect() # Desconectarse del broker
        client1.loop_stop()  # Finalizar el loop
        GPIO.cleanup()
        sys.exit()
