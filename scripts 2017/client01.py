import paho.mqtt.client as mqtt  #import the client1
import time
import RPi.GPIO as GPIO

# Pin Definitions
ledPin = 11
swPin = 13

# Pin Setup

GPIO.setmode(GPIO.BOARD) # BOARD pin-numbering scheme 
GPIO.setup(ledPin, GPIO.OUT) # LED Pin set as OUTput
GPIO.setup(swPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Switch Pin set as INput

swBool = GPIO.input(swPin)


def on_connect(client, userdata, flags, rc):
    m="Connected flags"+str(flags)+"result code "\
    +str(rc)+"  client1_id  "+str(client)
    print(m)

def on_message(client1, userdata, message):
    print("message received  "  ,str(message.payload.decode("utf-8")))

broker_address="192.168.0.103" #direccion computadora windows broker

client1 = mqtt.Client("P1")    #create new instance
client1.on_connect= on_connect        #attach function to callback
client1.on_message=on_message        #attach function to callback
time.sleep(1)
client1.connect(broker_address)      #connect to broker
client1.loop_start()    #start the loop
client1.subscribe("s1/mm1/evFinalCarga1")
client1.publish("s1/mm1/evFinalCarga1", "este es "+str(swBool))
time.sleep(5)

client1.disconnect()
client1.loop_stop()

GPIO.cleanup() # Cleanup all GPIO

