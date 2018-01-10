# prueba.py Sackett 2, 4 enero 2018  
# Publicar Reles Sackett 2 IP: 192.168.100.7

import paho.mqtt.client as mqtt  #import the client1
import time
import RPi.GPIO as GPIO
import sys 

# Pin Definitions
R12 = 17 # Carga 1
R14 = 27 # Descarga 1
R22 = 10 # Carga 2
R24 = 9 # Descarga 2
# Pin Setup. IN=1 con 3.3 V
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) # BCM Broadcom GPIO number scheme 
GPIO.setup(R12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # P17 INput
GPIO.setup(R14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # P27 INput
GPIO.setup(R22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # P10 INput
GPIO.setup(R24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # P9 INput



# MQTT
def on_connect(client, userdata, flags, rc):
    m="Connected flags"+str(flags)+"result code "\
    +str(rc)+"  client1_id  "+str(client)
    print(m)
def on_message(client1, userdata, message):
    print("message received  " + message.topic + " valor:  " + str(message.payload.decode("utf-8")))
    
broker_address="192.168.100.7" #IP RPi Sackett2
client1 = mqtt.Client("P1") # create new instance
client1.on_connect= on_connect # attach function to callback
client1.on_message=on_message #attach function to callback

# Conecta MQTT  
client1.connect(broker_address, 1883, 60) # connect to broker

# Topicos 
client1.subscribe([("s1/r12",0),("s1/r14",0)]) 
client1.subscribe([("s1/r22",0),("s1/r24",0)])

# Loop
client1.loop_start()    #start the loop
time.sleep(.1) #para 1/10 segundo
while True:
    try:
        # Lee GPIO
        bR12 = GPIO.input(R12) # bit Carga1
        bR14 = GPIO.input(R14) # bit Desc1
        bR22 = GPIO.input(R22) # bit Carga2
        bR24 = GPIO.input(R24) # bit Desc2      
        # Publica valores
        client1.publish("s1/r12", str(bR12)) # Carga1
        client1.publish("s1/r14", str(bR14)) # Desc1
        client1.publish("s1/r22", str(bR22)) # Carga2
        client1.publish("s1/r24", str(bR24)) # Desc2
        time.sleep(0.2) # Reduce ruido en medicion 
               
    except (KeyboardInterrupt, SystemExit):
        client1.disconnect() # Desconectarse del broker
        client1.loop_stop()  # Finalizar el loop
        GPIO.cleanup() # Cleanup all GPIO
        sys.exit() # Apaga el programa
