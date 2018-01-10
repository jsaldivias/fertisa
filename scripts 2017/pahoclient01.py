# pahoclient01.py
# m en español. P1 a SACKET1. sleep variable
# bulb1 variable. publish con variable

import paho.mqtt.client as mqtt  #import the client1
import time

def on_connect(client, userdata, flags, rc):
    m="BANDERAS "+str(flags)+"  CODIGO CR  "\
    +str(rc)+"  CLIENTE    "+str(client) \
    +"  USER DATA    "+str(userdata)
    print(m)

def on_message(client1, userdata, message):
    print("   PUBLICADO   "  ,str(message.payload.decode("utf-8")))

broker_address="192.168.0.103"
client1 = mqtt.Client("SACKET1")    #create new instance
client1.on_connect= on_connect        #attach function to callback
client1.on_message=on_message        #attach function to callback
time.sleep(0.1)
client1.connect(broker_address)      #connect to broker
client1.loop_start()    #start the loop
client1.subscribe("house/bulbs/bulb1")
bulb1="OFF"
client1.publish("house/bulbs/bulb1",bulb1)
time.sleep(.5)
bulb1="PRENDIDO"
client1.publish("house/bulbs/bulb1",bulb1)
time.sleep(.5)
bulb1="APAGADO DE NUEVO"
client1.publish("house/bulbs/bulb1",bulb1)
time.sleep(.5)
client1.disconnect()
client1.loop_stop()
