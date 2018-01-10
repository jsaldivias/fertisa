# pahoclient02.py
# lectura y publicacion de GPIO
# 

import paho.mqtt.client as mqtt  #import the client1
import time #libreria para medir el tiempo
import RPi.GPIO as GPIO #libreria para leer GPIO

evFinalCarga1 = 27
evFinalCarga2 = 4
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(evFinalCarga1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(evFinalCarga2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def on_connect(client, userdata, flags, rc):
    m="BANDERAS "+str(flags)+"  CODIGO CR  "\
    +str(rc)+"  CLIENTE    "+str(client) \
    +"  USER DATA    "+str(userdata)
    print(m)

def on_message(client1, userdata, message):
    print("   PUBLICADO   "  ,str(message.payload.decode("utf-8")))

R12 = GPIO.input(evFinalCarga1) # Lee R12 en Sacket1 del GPIO 27
R22 = GPIO.input(evFinalCarga2) # Lee R22 en Sacket1 del GPIO 4

broker_address="192.168.0.103"
client1 = mqtt.Client("SACKET1")    # Crea nueva instancia
client1.on_connect= on_connect  # Attach function to callback
client1.on_message=on_message   # Attach function to callback
time.sleep(0.1)

client1.connect(broker_address) # Connect to broker
client1.loop_start()    # Start the loop

client1.subscribe("s1/R12") # Crea topico R12 en Sacket1
client1.subscribe("s1/R22") # Crea topico R22 en Sacket1

strR12=str(R12) # Convierte en string valor leido
client1.publish("s1/R12",strR12) # Publica valor en topico
time.sleep(2)

strR22=str(R22) # Convierte en string valor leido
client1.publish("s1/R22",strR22) # Publica valor en topico
time.sleep(2)

client1.disconnect() # Desconectarse del broker
client1.loop_stop()  # Finalizar el loop
