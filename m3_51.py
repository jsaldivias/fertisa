#!/usr/bin/python3
# m3_51.py Sun 30/Sep/2018. 13.22 HRS.
# Paso 1. elimina todos los logger.
# Paso 2. Solo incluye q2 en mensajes.
#  

import paho.mqtt.client as mqtt
import time, sys, datetime, logging, sys
import RPi.GPIO as GPIO
import subprocess

def time_sync(iwsclock):
    """ Updates RPi time based on IWS time. Uses external command """
    dt0 = datetime.datetime.fromtimestamp(iwsclock)
    dt0s = '{:}'.format(dt0.strftime('%Y-%m-%d %H:%M:%S'))
    extcmd = "sudo date --set '{}'".format(dt0s)
    subprocess.call(extcmd, shell = True)

def setup_logger(name):
    """Setup loggers for each WO or WA"""
    log_file = "/home/pi/Documents/Logs/LOG{}{}".format(name, ".log")
    formatter = logging.Formatter('%(levelname)s -- %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

# LOG INITIAL. BY DEFAULT.
log_ope = setup_logger("m3log")

# ---- MQTT
broker_address="192.168.100.5"
mqtt.Client.connected_flag = False
pub_topic="m3/m3Qin"
message_queue = []

#Keycode. R: Relay. 1st#: Minimate.
#2nd#: 2 LG: Load Gate), 4 DG: Discharge Gate
R12, R14 = 17, 16 # LG[1] DG[1]
R22, R24 = 13, 18 # LG[2] DG[2]
R32, R34 = 18, 19 # LG[3] DG[3]
R42, R44 = 20, 21 # LG[4] DG[4]

# ---- Pin Setup
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

#WO Flag for Manual Init
WOIni = "0" #Manual Start 6-7

#WO List WO_L[]
SelNo,SelPro,SelQ1,SelStt,SelQ2 = "","",0,"",0
WO_L = [SelNo,SelPro,SelQ1,SelStt,SelQ2]

#Sack Counters for WO and WA
q_wa,q_wo  = 0,0

#Server IWS Clock and Delta
IWS_L = [0] #server IWS clock
iws_dT = 0.0  # Delta T

#Initial values previous WA-name and WA-date
wa_prev, wa_date_prev = 'nd', 'nd'

def call_time():
    """Returns IWS server time as list"""

    t0 = datetime.datetime.fromtimestamp(time.time() + iws_dT)
    YY, MM, DD = t0.year, str(t0.month).zfill(2), str(t0.day).zfill(2)
    hh, mm = str(t0.hour).zfill(2), str(t0.minute).zfill(2)
    ss = str(t0.second).zfill(2)
    wa_date = '{}-{}-{}-'.format(DD, MM, YY)
    wa_time = '{}{}h{}m'.format(wa_date, hh, mm)
    log_time = '{}-{}-{} {}:{}:{} '.\
               format(YY,MM,DD,hh,mm,ss)
    t_return = [wa_date, wa_time, log_time]
    return t_return

def call_wa():
    global logger
    """ Creates WA with IWS time.
        1: Day passed: new "wa_name", 0 to "qty".
        2: Same day WA: same "wa", same "q_wa"
        Uses external: "q_wa", "wa_date_prev"
        Returns: wa_name, wa_date, qty """

    wa_date, wa_time, log_time = call_time()
    if wa_date != wa_date_prev:
        wa_name ='{}{}'.format("A-FN43-", wa_time)
        qty = 0
        #logger = setup_logger(wa_name)
    else:
        wa_name = wa_prev
        qty = q_wa
    wa_return = [wa_name, wa_date, qty]
    return wa_return

#Initial DICTIONARY with time data
t0 = time.time() #initial time
bin1 = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0,\
        "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0 }
bin2 = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0,\
        "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0 }
bin3 = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0,\
        "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0 }
bin4 = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0,\
        "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0 }

def clean_bin(bin):
    """ Set bin dictionaries to Initial conditions"""

    t0 = time.time()
    bin = {"LG": False, "LG_Prev": False, "LG_T1": t0, "LG_T2": t0,\
           "DG": False, "DG_Prev": False, "DG_T1": t0, "DG_T2": t0 }

#-- PUBLISH DATA
def pub_data():
    """ Retrieve messages from queue and publish,
        if connected, as long as queue is not empty  """
    if client.connected_flag:
        while len(message_queue) > 0:
            m_out = message_queue.pop(0)
            client.publish("m3/m3Qin", m_out, 1)
    else:
        m = "Messages in queue = {}".format(len(message_queue))
        print(m)
        logger.debug(m)

#-- ON CONNECT
def on_connect(client, userdata, flags, rc):
    """ If succesful connected, connected_flag True. Can publish."""
    if rc == 0:
        client.connected_flag = True
    else:
        print("MALA CONEXION. CODIGO: {}".format(rc))

#-- ON DISCONNECT
def on_disconnect(client, userdata, rc):
    """ Sets "connected flag" to False. Preventing publish """
    client.connected_flag = False

#-- ON LOG
def on_log(client, userdata, level, buf):
    """ Events of communication via MQTT """
    #wa_date, wa_time, log_time = call_time()
    #m = "--{} {}--".format(log_time, buf)
    m = "--{}--".format( buf)
    print(m)
    #log_ope.debug(m)

#-- CHECK GATES STATUS
def check_status(bin,x):
    """ Read LG and DG Status. Both open: Cleaning.
    Rising: goes False to True. Falling: True to False.
    LG(DG) Rising: LG_T1. LG(DG) Falling: LG_T2.
    Duration: T2 - T1. DG closes and Duration > 1 sec, counts sack."""
    global q_wo, SelNo, SelPro, SelQ1, q_wa, wa_date,\
           wa_mach, wa_date_prev, wa_prev, logger

    #--ON CLEANING
    if bin["LG"] and bin["DG"]:
        clean_bin(bin)
        #time.sleep(1)
        return

    #-- LG Rising
    if bin["LG"] and not bin["LG_Prev"]:
        bin["LG_T1"] = time.time()
        print(" Carga {}".format( x))

    #-- LG Falling
    if not bin["LG"] and bin["LG_Prev"]:
        bin["LG_T2"] = time.time()
        print("Fin Carga {}".format( x))

    #-- DG Rising
    if bin["DG"]and not bin["DG_Prev"]:
        bin["DG_T1"] = time.time()
        print("DESCARGA {}".format( x))

    #-- DG Falling. END CYCLE
    if not bin["DG"] and bin["DG_Prev"]:
        bin["DG_T2"] = time.time()
        print("Fin DESCarga {}".format( x))

        #DELTA 'EM
        LG_dT = bin["LG_T2"] - bin["LG_T1"]
        DG_dT = bin["DG_T2"] - bin["DG_T1"]
        cycle = bin["DG_T2"] - bin["LG_T1"]

        #'EM FRESH? TODAY'S
##        if LG_dT > 36000:
##            LG_dT = 0
##        if DG_dT > 36000:
##            DG_dT = 0
##        if cycle > 36000:
##            cycle = 0

        #STRING 'EM
##        lg_open = '{:0.1f}'.format(LG_dT)
##        dg_open = '{:0.1f}'.format(DG_dT)
##        ctime = '{:0.1f}'.format(cycle)

        #COUNT 'EM
        if LG_dT > 1 and DG_dT > 1:

            # WO: SelNo IS ALL NUMBERS
            if SelNo.isnumeric():
                print("En Rutina WO= {} valor numerico. q_wo= {}".format(SelNo, q_wo))
                q_wo += 1
                msg_out = "{}///////".format(q_wo)
                print("msg_out saco de WO: {}".format(msg_out))

            # WA: SelNo STARTS WITH "A"
            if SelNo.startswith("A"):
                print("En Rutina SelNo= {} iniciaAAAAA con A. q_wa= {}, q_wo= {}".format(SelNo, q_wa, q_wo))
##                wa_prev, wa_date_prev, q_wa = call_wa()
##                SelNo = wa_prev
                q_wo += 1
##                q_wo = q_wa 
                print("Despues de sumar. q_wo= {} q_wa = {}, ".format( q_wo, q_wa))
                msg_out = "{}///////".format(q_wo)
                print("msg_out saco Admin: {}".format(msg_out))

            # BLANK WO: SelNo NOT SELECTED WO
            if SelNo == "":
                print("En Rutina cuando SelNo= [{}] en blancOOOOO".format(SelNo))
                wa_prev, wa_date_prev, q_wa = call_wa()
                SelNo, wa_date_prev, q_wa = call_wa()
##                q_wa += 1
                q_wo = q_wa + 1
##                q_wo,SelNo,SelPro,SelQ1 = q_wa,wa_prev,"Por llenar",100
                msg_out = "{}/////{}/Por llenar/100".format(q_wo, SelNo)
                print("Crear WA: {}".format(msg_out))

            #MESSAGE 'EM
##            msg_out = "{}/{}/{}/{}/{}/{}/{}/{}".\
##                      format(q_wo, ctime, x, lg_open, \
##                             dg_open, SelNo, SelPro, SelQ1)
            message_queue.append(msg_out)
            pub_data()
            #wa_date, wa_time, log_time = call_time()
##            m1 = " Q:{} / dT:{} / MM:{} / LG:{} / ".\
##                  format(q_wo, ctime, x, lg_open)
##            m2 = "DG:{} / WO:{} / Prod:{} / Q1:{}".\
##                  format(dg_open, SelNo, SelPro, SelQ1)
##            #m = log_time + m1 + m2
##            m =  m1 + m2
##            print(m)
##            logger.debug(m)

        #dT ZERO 'EM
        #MAKE LG dT Previous =0.
        bin["LG_T2"] = bin["DG_T2"]
        bin["LG_T1"] = bin["DG_T2"]

    #PREVIOUS 'EM
    bin["LG_Prev"] = bin["LG"]
    bin["DG_Prev"] = bin["DG"]

#-- ON MESSAGE
def on_message(client, userdata, message):
    """ 4 MQTT:  m3WO1: WO Data.  m3DT: server clock.
    m3WOIni: WO Initiate.  m3WOEnd: WO End."""
    global iws_dT, WOIni, q_wo, WO_Select, WO_L, SelNo,\
           SelPro, SelQ1, bin1, bin2, bin3, bin4, logger

    topic = message.topic.split("/")
    payload = str(message.payload.decode("utf-8"))

    # WO from IWS. WO_L = [WO,Pro,Q1,Stt,Q2]
    if topic[1] == "m3WO1":
        WO_L  = payload.split("/")
        print("Datos desde Base de Datos IWS: {}".format(WO_L))

    # CLOCK SYNC
    if topic[1] == "m3DT":
        time_sync(float(payload)) 

    # woIni BY OPERATOR.
    if topic[1] == "m3WOIni":
        if payload == "7":
            SelNo,SelPro,SelQ1,SelStt,SelQ2 = WO_L
            q_wo = 0
            #logger = setup_logger(SelNo)
            #--CLEAN UP BINS
            clean_bin(bin1)
            clean_bin(bin2)
            clean_bin(bin3)
            clean_bin(bin4)
            print("Inicio de Orden del Operador")

    #-- WO END
    if topic[1] == "m3WOEnd":
        if payload == "1":
            q_wo,SelNo,SelPro,SelQ1 = 0,"","",0
            print("FIN de ORDEN")

# ---- Instanciate - Attach to callback
client = mqtt.Client(client_id = "m3py")
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
        time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        client.disconnect()
        client.loop_stop()
        GPIO.cleanup()
        sys.exit()
