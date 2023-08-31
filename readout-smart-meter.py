#  readout-smart-meter.py
#  ======================
#  Script which readouts the smart meter via M-Bus.
#  Readout happens every 5 seconds (set by electricity provider).
#
import serial
import os
import signal
import sys
import time
import traceback
from binascii import unhexlify
from datetime import datetime
from gurux_dlms.GXByteBuffer import GXByteBuffer
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
import lxml, cchardet  # needs to be installed and imported for better performance with BeautifulSoup - possibly needs package cython being installed
from bs4 import BeautifulSoup

# -- CONFIGURATION BEGIN -- #

# SERIAL COMMUNICATION
COM_PORT = "/dev/ttyUSB0"
BAUDRATE = 2400
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
BYTESIZE = serial.EIGHTBITS
TIMEOUT = 3  # As the meter sends data every 5s the timeout must be <5s

# SMART METER MESSAGE - SPECIFIC
FRAME_LENGTH = 376
# Message consists of 2 frames.
FRAME1_START_BYTE = b"\x68"
FRAME2_END_BYTE = b"\x16"
# AES key format, e.g. 48E2C...
VNB_KEY = "<YOUR_KEY>"

LOG_FILE = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__), os.path.basename(__file__)[:-2]+"log"))
# LOG_FILE = ""  # if you don't want to log
PRINT_LOGS = True

# -- CONFIGURATION END -- #

# OBIS = {
#     "0.0.1.0.0.255":  "Datum und Uhrzeit",
#     "0.0.96.1.0.255": "Zählernummer des Netzbetreibers",
#     "0.0.42.0.0.255": "COSEM logical device name",
#     "1.0.32.7.0.255": "Spannung L1",
#     "1.0.52.7.0.255": "Spannung L2",
#     "1.0.72.7.0.255": "Spannung L3",
#     "1.0.31.7.0.255": "Strom L1",
#     "1.0.51.7.0.255": "Strom L2",
#     "1.0.71.7.0.255": "Strom L3",
#     "1.0.1.7.0.255":  "Wirkleistung Bezug +P",
#     "1.0.2.7.0.255":  "Wirkleistung Lieferung -P",
#     "1.0.1.8.0.255":  "Wirkenergie Bezug +A (Wh)",
#     "1.0.2.8.0.255":  "Wirkenergie Lieferung -A (Wh)",
#     "1.0.3.8.0.255":  "Blindenergie Bezug +R (Wh)",
#     "1.0.4.8.0.255":  "Blindenergie Lieferung -R (Wh)",
# }
OBIS_DATE = "0.0.1.0.0.255"
OBIS = {
    "1.0.32.7.0.255": "VoltageL1",
    "1.0.52.7.0.255": "VoltageL2",
    "1.0.72.7.0.255": "VoltageL3",
    "1.0.31.7.0.255": "CurrentL1",
    "1.0.51.7.0.255": "CurrentL2",
    "1.0.71.7.0.255": "CurrentL3",
    "1.0.1.7.0.255":  "RealPowerIn",
    "1.0.2.7.0.255":  "RealPowerOut",
    "1.0.1.8.0.255":  "RealEnergyIn",
    "1.0.2.8.0.255":  "RealEnergyOut",
    "1.0.3.8.0.255":  "ReactiveEnergyIn",
    "1.0.4.8.0.255":  "ReactiveEnergyOut",
}
OBIS_UNUSED = {
    "0.0.96.1.0.255": "MeterID",
    "0.0.42.0.0.255": "MeterType",
}


def log(msg, error=False):
    global LOG_FILE
    if error:
        msg = "ERROR: " + msg
    if PRINT_LOGS:
        print(msg, file=sys.stderr if error else None)
    if LOG_FILE:
        msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S - ") + str(os.getpid()) + ": " + msg
        with open(LOG_FILE, "a") as log_file:
            log_file.write("\n" + msg)


class SignalHandler:
    _shutdown = False
    _immediately = False

    def __init__(self, shutdown_immediately=False):
        self._immediately = shutdown_immediately
        signal.signal(signal.SIGINT, self._request_shutdown)
        signal.signal(signal.SIGTERM, self._request_shutdown)

    def _request_shutdown(self, *args):
        log('Request to shutdown received. Stopping...')
        self._shutdown = True
        if self._immediately:
            quit()

    def shutdown_requested(self):
        return self._shutdown


log("Start " + os.path.basename(__file__))

signalHandler = SignalHandler()

translator = GXDLMSTranslator()
translator.blockCipherKey = GXByteBuffer(VNB_KEY)
translator.comments = True
#translator.completePdu = True
translator.hex = False  # Shows numeric values as int instead of hex -> <UInt16 Value="2319" /> instead of <UInt16 Value="090F" />

ser = serial.Serial(
    port=COM_PORT,
    baudrate=BAUDRATE,
    parity=PARITY,
    stopbits=STOPBITS,
    bytesize=BYTESIZE,
    timeout=TIMEOUT
)

lastError = 0
errorCount = 0

while not signalHandler.shutdown_requested():
    try:
        data = ser.read(size=FRAME_LENGTH)

        if data == b"":
            continue

        if len(data) < FRAME_LENGTH and data[0:1] == FRAME1_START_BYTE and data[1:2] == data[2:3]:
            # log("Incomplete message received. Try to get rest... Len: " + str(len(data)))
            rest = ser.read(size=FRAME_LENGTH - len(data))
            if len(data) + len(rest) == FRAME_LENGTH:
                data = data + rest
                # log("Incomplete message completed. Len: " + str(len(data)))

        if len(data) < FRAME_LENGTH or data[0:1] != FRAME1_START_BYTE or data[-1:] != FRAME2_END_BYTE:
            log("Incomplete message received. Synchronize...")
            continue

        timestamp = int(time.time()) - 2

        # splitInfo = data[6]  # CI field - if this is x00, there's a second frame
        systemTitle = data[11:19]  # --- 8 bytes
        frameCounter = data[23:27]  # --- 4 bytes
        initVector = systemTitle + frameCounter  # --- 12 bytes

        payload1StartPos = 27
        payload2StartPos = 9

        frameLength1 = int(hex(data[1]), 16)  # FA --- 250 bytes
        frameLength2 = int(hex(data[frameLength1 + 7]), 16) # FA --- 38 Byte

        payload1 = data[payload1StartPos:(6 + frameLength1 - 2)]  # 6: Start bytes (M-Bus Data link layer) 2: end character + checksum
        payload2 = data[6 + frameLength1 + payload2StartPos:(frameLength1 + 5 + 5 + frameLength2)]

        cypherText = payload1 + payload2

        aesgcm = AESGCM(unhexlify(VNB_KEY))
        apdu = aesgcm.encrypt(initVector, cypherText, b"0").hex()

        xml = translator.pduToXml(apdu)
        soup = BeautifulSoup(xml, "lxml")

        # -> Do not use Smart Meter's time as it's about 20 seconds behind (in my case)
        # date = soup.find("datetime")
        # if not date:
        #     log("Could not retrieve datetime.", True)
        #     continue
        # date = date["value"]
        # year = int(date[0:4], 16)
        # month = int(date[4:6], 16)
        # day = int(date[6:8], 16)
        # hour = int(date[10:12], 16)
        # minute = int(date[12:14], 16)
        # second = int(date[14:16], 16)
        # #hundredthSecond = int(datetime[16:18], 16)
        # timestamp = int(datetime(year, month, day, hour, minute, second).timestamp())

        data = {}

        # Safer approach which analyzes the OBIS codes and does not depend on the order of the values
        elements = soup.find("structure").find_all("structure", recursive=False)
        for el in elements:
            obisCode = el.find("octetstring")["value"]
            obisCode = ".".join("{!s}".format(int(obisCode[i:i+2], 16)) for (i) in range(0, 11, 2))
            if obisCode in OBIS:
                type = OBIS[obisCode]
                value = el.find("uint16") or el.find("uint32")
                if value and value["value"]:
                    data[type] = int(value["value"])
            elif obisCode != OBIS_DATE and obisCode not in OBIS_UNUSED:
                log("Message contains new and untracked OBIS code: " + obisCode)

        if len(data) == len(OBIS):
            print(os.linesep.join([
                "",
                "Timestamp:         " + datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                "VoltageL1:         " + str(data["VoltageL1"] / 10) + " V",
                "VoltageL2:         " + str(data["VoltageL2"] / 10) + " V",
                "VoltageL3:         " + str(data["VoltageL3"] / 10) + " V",
                "CurrentL1:         " + str(data["CurrentL1"] / 100) + " A",
                "CurrentL2:         " + str(data["CurrentL2"] / 100) + " A",
                "CurrentL3:         " + str(data["CurrentL3"] / 100) + " A",
                "RealPower:         " + str(data["RealPowerIn"]-data["RealPowerOut"]) + " W",
                "RealPowerIn:       " + str(data["RealPowerIn"]) + " W",
                "RealPowerOut:      " + str(data["RealPowerOut"]) + " W",
                "RealEnergyIn:      " + str(data["RealEnergyIn"] / 1000) + " kWh",
                "RealEnergyOut:     " + str(data["RealEnergyOut"] / 1000) + " kWh",
                "ReactiveEnergyIn:  " + str(data["ReactiveEnergyIn"] / 1000) + " kvar",
                "ReactiveEnergyOut: " + str(data["ReactiveEnergyOut"] / 1000) + " kvar",
            ]))
        else:
            log("Only " + str(len(data)) + " values found in message" + (
                ": " + ",".join(data.keys()) if len(data) > 0 else ""), True)

        # Unsafer (and not really faster according to test) approach which depends on the order of the values sent
        # results_16 = soup.find_all("uint16")
        # results_32 = soup.find_all("uint32")
        #
        # if len(results_16) < 6 or len(results_32) < 6:
        #     log("Too little values found in message.", True)
        # else:
        #     print("Timestamp:", datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"))
        #     for key in data:
        #         print(key + ": ", data[key])

    except Exception as e:
        log(str(e), True)
        log(traceback.format_exc(), True)
        if lastError < time.time() - 300:
            errorCount = 1
        else:
            errorCount = errorCount + 1
        if errorCount > 5:
            log("Too many errors occurred. Shutdown...", True)
            break
        lastError = time.time()

ser.close()
