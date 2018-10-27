#!/usr/bin/python3
# S2_50.py Sun 30/Sep/2018. 10.03 HRS.
# Sync time in RPi with clock in IWS Server
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
log_ope = setup_logger("s2log")

# ---- MQTT
broker_address="192.168.100.5"
mqtt.Client.connected_flag = False
pub_topic="s2/s2Qin"
message_queue = []

#Keycode. R: Relay. 1st#: Minimate.
#2nd#: 2 LG: Load Gate), 4 DG: Discharge Gate
R12, R14 = 17, 22 #  LG[1] DG[1]
R22, R24 = 10, 9 #   LG[2] DG[2]

# ---- Pin Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) # BCM scheme
GPIO.setup(R12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(R14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(R22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(R24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#WO Flag for Manual Init
WOIni = "0"  #Manual Start 6-7

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
        wa_name ='{}{}'.format("A-S2-", wa_time)
        qty = 0
        logger = setup_logger(wa_name)
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
        while len(message_queue)>0:
            m_out=message_queue.pop(0)
            client.publish("s2/s2Qin", m_out, 1)
    else:
        m="Messages in queue ={}".format(len(message_queue))
        print(m)
        logger.debug(m)

# ---ON CONNECT
def on_connect(client, userdata, flags, rc):
    """ If succesful connected, connected_flag True. Can publish."""
    if rc==0:
        client.connected_flag=True
    else:
        print("MALA CONEXION. CODIGO: ", rc)

#-- ON DISCONNECT
def on_disconnect(client, userdata, rc):
    """ Sets "connected flag" to False. Preventing publish """
    client.connected_flag=False

#-- ON LOG
def on_log(client, userdata, level, buf):
    """ Events of communication via MQTT """
    wa_date, wa_time, log_time = call_time()
    m = "--{} {}--".format(log_time, buf)
    print(m)
    log_ope.debug(m)

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

    #--LG RISING
    if bin["LG"] and not bin["LG_Prev"]:
        bin["LG_T1"]=time.time()

    #-- LG FALLING
    if not bin["LG"] and bin["LG_Prev"] :
        bin["LG_T2"]=time.time()

    #--DG RISING
    if bin["DG"]and not bin["DG_Prev"]:
        bin["DG_T1"]=time.time()

    #--DG FALLING. END CYCLE
    if not bin["DG"] and bin["DG_Prev"]:
        bin["DG_T2"]=time.time()

        #DELTA 'EM
        LG_dT=bin["LG_T2"]-bin["LG_T1"]
        DG_dT=bin["DG_T2"]-bin["DG_T1"]
        cycle=bin["DG_T2"]-bin["LG_T1"]

        #'EM FRESH? TODAY'S
        if LG_dT>36000:
            LG_dT=0
        if DG_dT>36000:
            DG_dT=0
        if cycle>36000:
            cycle=0

        #STRING 'EM
        lg_open='{:0.1f}'.format(LG_dT)
        dg_open='{:0.1f}'.format(DG_dT)
        ctime='{:0.1f}'.format(cycle)

        #COUNT 'EM
        if LG_dT>0.5 and DG_dT>0.5:

            # WO: SelNo IS ALL NUMBERS
            if SelNo.isnumeric():
                q_wo += 1

            # WA: SelNo STARTS WITH "A"
            if SelNo.startswith("A"):
                wa_prev, wa_date_prev, q_wa = call_wa()
                SelNo = wa_prev
                q_wa += 1
                q_wo = q_wa

            # BLANK WO: SelNo NOT SELECTED WO
            if SelNo == "":
                wa_prev, wa_date_prev, q_wa = call_wa()
                q_wa += 1
                q_wo,SelNo,SelPro,SelQ1 = q_wa,wa_prev,"Por llenar",100

        #MESSAGE 'EM
            msg_out = "{}/{}/{}/{}/{}/{}/{}/{}".\
                      format(q_wo, ctime, x, lg_open, \
                             dg_open, SelNo, SelPro, SelQ1)
            message_queue.append(msg_out)
            pub_data()
            wa_date, wa_time, log_time = call_time()
            m1 = " Q:{} / dT:{} / MM:{} / LG:{} / ".\
                  format(q_wo, ctime, x, lg_open)
            m2 = "DG:{} / WO:{} / Prod:{} / Q1:{}".\
                  format(dg_open, SelNo, SelPro, SelQ1)
            m = log_time + m1 + m2
            print(m)
            logger.debug(m)

        #dT ZERO 'EM
        #MAKE LG dT Previous =0.
        bin["LG_T2"]=bin["DG_T2"]
        bin["LG_T1"]=bin["DG_T2"]

    #PREVIOUS 'EM
    bin["LG_Prev"] = bin["LG"]
    bin["DG_Prev"] = bin["DG"]

#-- ON MESSAGE
def on_message(client, userdata, message):
    """ 4 MQTT:  s2WO1: WO Data.  s2DT: server clock.
    s2WOIni: WO Initiate.  s2WOEnd: WO End."""
    global iws_dT, WOIni, q_wo, WO_Select, WO_L, SelNo,\
           SelPro, SelQ1, bin1, bin2, bin3, bin4, logger

    topic = message.topic.split("/")
    payload = str(message.payload.decode("utf-8"))

    # WO from IWS. WO_L = [WO,Pro,Q1,Stt,Q2]
    if topic[1] == "s2WO1":
        WO_L  = payload.split("/") 

    # CLOCK SYNC
    if topic[1] == "s2DT":
        time_sync(float(payload))

    # woIni BY OPERATOR.
    if topic[1] == "s2WOIni":
        if payload == "7":
            SelNo,SelPro,SelQ1,SelStt,SelQ2 = WO_L
            q_wo = 0
            logger = setup_logger(SelNo)
            #--CLEAN UP BINS
            clean_bin(bin1)
            clean_bin(bin2)

    #-- WO END
    if topic[1] == "s2WOEnd":
        if payload == "1":
            q_wo,SelNo,SelPro,SelQ1 = 0,"","",0

# ---- Instanciate - Attach to callback
client = mqtt.Client(client_id="s2py")
client.on_connect = on_connect
client.on_disconnect=on_disconnect
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
client.subscribe("s2/s2DT",1)
client.subscribe("s2/s2WO1",1)
client.subscribe("s2/s2WOIni",1)
client.subscribe("s2/s2WOEnd",1)

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
        check_status(bin1,1)
        check_status(bin2,2)
        time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        client.disconnect()
        client.loop_stop()
        GPIO.cleanup()
        sys.exit()
