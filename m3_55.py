#!/usr/bin/python3
# m3_55.py Tue 02/Oct/2018. 12.26 HRS.
# Variable LG_dT, DG_dT agregada al Diccionario
# Los tiempos de monitoreo LG y DG se reducen.
#

import paho.mqtt.client as mqtt
import time, sys, datetime, logging, sys
import RPi.GPIO as GPIO
import subprocess

def time_sync(iwsclock):
    """ Actualiza reloj Raspberry """
    dt0 = datetime.datetime.fromtimestamp(iwsclock)
    dt0s = '{:}'.format(dt0.strftime('%Y-%m-%d %H:%M:%S'))
    extcmd = "sudo date --set '{}'".format(dt0s)
    subprocess.call(extcmd, shell = True)

# ---- MQTT
broker_address="192.168.100.5"
mqtt.Client.connected_flag = False
pub_topic="m3/m3Qin"
message_queue = []
#----Keycode.
R12, R14 = 17, 16 # LG[1] DG[1]
R22, R24 = 13, 18 # LG[2] DG[2]
R32, R34 = 18, 19 # LG[3] DG[3]
R42, R44 = 20, 21 # LG[4] DG[4]
#---- Pin Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(R12, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(R14, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(R22, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(R24, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(R32, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(R34, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(R42, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(R44, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
#--- Flag Operador Inicia Orden WO
WOIni = "0" #Manual Start 6-7
#--- Data recibido del Servidor. WO_L[]
SelNo,SelPro,SelQ1,SelStt,SelQ2 = "","",0,"",0
WO_L = [SelNo, SelPro, SelQ1, SelStt, SelQ2]
#----Contadores de Sacos para WO y WA
q_wa,q_wo  = 0,0
#----Inicializacion de Valores
wa_prev, wa_date_prev = 'nd', 'nd'
#Initial DICTIONARY with time data
t0 = time.time() #initial time
bin1 = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0, "LG_dT": 0,\
        "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0, "DG_dT": 0}
bin2 = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0, "LG_dT": 0,\
        "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0, "DG_dT": 0}
bin3 = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0, "LG_dT": 0,\
        "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0, "DG_dT": 0}
bin4 = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0, "LG_dT": 0,\
        "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0, "DG_dT": 0}

def call_time():
    """Formato Fecha-Hora para Ordenes Administrativas"""
    t0 = datetime.datetime.fromtimestamp(time.time())
    YY, MM = t0.year, str(t0.month).zfill(2)
    DD = str(t0.day).zfill(2)
    hh, mm = str(t0.hour).zfill(2), str(t0.minute).zfill(2)
    ss = str(t0.second).zfill(2)
    wa_date = '{}-{}-{}-'.format(DD, MM, YY)
    wa_time = '{}{}h{}m'.format(wa_date, hh, mm)
    t_return = [wa_date, wa_time]
    return t_return

def call_wa():
    """ Creates WA with IWS time."""
    wa_date, wa_time = call_time()
    if wa_date != wa_date_prev:
        wa_name ='{}{}'.format("A-FN43-", wa_time)
        qty = 0
    else:
        wa_name = wa_prev
        qty = q_wa
    wa_return = [wa_name, wa_date, qty]
    return wa_return

def clean_bin(bin):
    """ Borrar contenido del bin """
    t0 = time.time()
    bin = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0, "LG_dT": 0,\
           "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0, "DG_dT": 0}

def pub_data():
    """ Retrieve messages from queue and publish  """
    if client.connected_flag:
        while len(message_queue) > 0:
            m_out = message_queue.pop(0)
            client.publish("m3/m3Qin", m_out, 1)
    else:
        m = "Messages in queue = {}".format(len(message_queue))
        print(m)

def on_connect(client, userdata, flags, rc):
    """ connected_flag True. Can publish."""
    if rc == 0:
        client.connected_flag = True
    else:
        print("MALA CONEXION. CODIGO: {}".format(rc))

def on_disconnect(client, userdata, rc):
    """ connected flag to False. Cannot publish """
    client.connected_flag = False

def on_log(client, userdata, level, buf):
    """ Events of communication via MQTT """
    m = "--{}--".format( buf)
    print(m)

def check_status(bin,x):
    """ LG and DG Status. """
    global q_wo, SelNo, SelPro, SelQ1, q_wa, wa_date,\
           wa_mach, wa_date_prev, wa_prev
    if bin["LG"] and bin["DG"]: #--ON CLEANING
        clean_bin(bin)
        return
    elif bin["LG"] and not bin["LG_Prev"]: #-- LG Open
        bin["LG_T1"] = time.time()
        print(" Carga {}".format(x))
    elif not bin["LG"] and bin["LG_Prev"]: #-- LG Close
        bin["LG_T2"] = time.time()
        bin["LG_dT"] = time.time() - bin["LG_T1"]
        print("Fin Carga {}".format(x))
    elif bin["DG"] and not bin["DG_Prev"]: #-- DG Open
        bin["DG_T1"] = time.time()
        print("DESCARGA {}".format( x))
    elif not bin["DG"] and bin["DG_Prev"]: #-- DG Close
        bin["DG_T2"] = time.time()
        bin["DG_dT"] = time.time() - bin["DG_T1"]
        print("Fin DESCarga {}".format( x))
        if bin["LG_dT"] > 0.5 and bin["DG_dT"]>0.3: #-- Count
            if SelNo.isnumeric(): #-- WO
                q_wo += 1
                msg_out = "{}///////".format(q_wo)
                print("msg_out saco de WO: {}".format(msg_out))
            if SelNo.startswith("A"): #-- WA
                q_wa += 1
                msg_out = "{}///////".format(q_wa)
                print("msg_out saco Admin: {}".format(msg_out))
            if SelNo == "": #-- New WA
                SelNo, wa_date_prev, q_wa = call_wa()
                q_wa += 1
                msg_out = "{}/////{}/Por llenar/100".format(q_wa, SelNo)
            message_queue.append(msg_out)
            pub_data()
        else:
            bin["LG_dT"] = 0
    bin["LG_Prev"] = bin["LG"] #Actualiza status Previo
    bin["DG_Prev"] = bin["DG"]

def on_message(client, userdata, message):
    """ 4 MQTT:  m3WO1: WO Data.  m3DT: server clock.
    m3WOIni: WO Initiate.  m3WOEnd: WO End."""
    global WOIni, q_wo, WO_Select, WO_L, SelNo,\
           SelPro, SelQ1, bin1, bin2, bin3, bin4
    topic = message.topic.split("/")
    payload = str(message.payload.decode("utf-8"))
    if topic[1] == "m3WO1":     # [WO,Pro,Q1,Stt,Q2]
        WO_L  = payload.split("/")
        print("Datos desde Base de Datos IWS: {}".format(WO_L))
    if topic[1] == "m3DT": # CLOCK SYNC
        time_sync(float(payload))
    if topic[1] == "m3WOIni": # woInitiated
        if payload == "7":
            SelNo,SelPro,SelQ1,SelStt,SelQ2 = WO_L
            q_wo = 0
            clean_bin(bin1)
            clean_bin(bin2)
            clean_bin(bin3)
            clean_bin(bin4)
            print("Inicio de Orden del Operador")
    if topic[1] == "m3WOEnd": #-- WO Ended
        if payload == "1":
            q_wo,SelNo,SelPro,SelQ1 = 0,"","",0
            print("FIN de ORDEN")
# ---- Instanciate - Attach to callback
client = mqtt.Client(client_id = "m3pyB")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_log = on_log
# ---- Connect MQTT
try:
    client.connect(broker_address, 1883, 60)
except:
    m = "NO SE PUEDE CONECTAR "
    print(m)
    sys.exit(1)
time.sleep(1)
# ---- Suscription
client.subscribe("m3/m3DT",1)
client.subscribe("m3/m3WO1",1)
client.subscribe("m3/m3WOIni",1)
client.subscribe("m3/m3WOEnd",1)
# ---- Loop
client.loop_start()
time.sleep(1)
# ---- Main Program
while True:
    try:
        bin1["LG"] = GPIO.input(R12)
        bin1["DG"] = GPIO.input(R14)
        bin2["LG"] = GPIO.input(R22)
        bin2["DG"] = GPIO.input(R24)
        bin3["LG"] = GPIO.input(R32)
        bin3["DG"] = GPIO.input(R34)
        bin4["LG"] = GPIO.input(R42)
        bin4["DG"] = GPIO.input(R44)
        check_status(bin1,1)
        check_status(bin2,2)
        check_status(bin3,3)
        check_status(bin4,4)
        time.sleep(0.02)
    except (KeyboardInterrupt, SystemExit):
        client.disconnect()
        client.loop_stop()
        GPIO.cleanup()
        sys.exit()
