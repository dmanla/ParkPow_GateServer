import RPi.GPIO as GPIO
import time
import os, sys
from flask import Flask
from flask import request
import json
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

gate1_AccessList = ['sgd6707b', 'sgd6707g']
gate2_AccessList = ['sjf5117p', 'sjf5117g']

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.OUT)
GPIO.setup(6, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)

GPIO.output(5,True)
GPIO.output(6,True)
GPIO.output(13,True)
time.sleep(1)
GPIO.output(13,False)

def updateAccessList():
    accessListLocation = os.path.join(sys.path[0], 'configDir/accessList.csv')
    GPIO.output(13, True)
    with open (accessListLocation, "r") as accessListFile:
        gate1_AccessList.clear()
        gate2_AccessList.clear()
        for accessRecord in accessListFile:
            access1, access2 = accessRecord.split(',')
            gate1_AccessList.append(access1)
            gate2_AccessList.append(access2.replace("\n", ""))

    time.sleep(2)
    GPIO.output(13, False)
#---------------Get Configuration Data-----------------#
configLocation = os.path.join(sys.path[0], 'configDir/config.ini')
configValues = {}
with open (configLocation, "rt") as configFile:
    for configValue in configFile:
        key, value = configValue.split('= ')
        configValues[key] = value

gateOpenPeriod = int(configValues.get('gate-open-period'))
pollFrequency = int(configValues.get('poll-frequency'))
apiToken = configValues.get('api-token')
#-------------------------------------------------------#

scheduler = BackgroundScheduler()
scheduler.add_job(func=updateAccessList, trigger="interval", seconds=pollFrequency)
scheduler.start()

@app.route('/postJson', methods = ['POST'])
def postJsonHandler():
    jsonData = request.form['json']
    parsedJson = json.loads(jsonData)
    plateNumber  = parsedJson['data']['results'][0]['plate']
    print(plateNumber)
    if plateNumber in gate1_AccessList:
        print("{} routed to GATE 1".format(plateNumber))
        GPIO.output(5,False)
        time.sleep(gateOpenPeriod)
        GPIO.output(5,True)
    elif plateNumber in gate2_AccessList:
        print("{} routed to GATE 2".format(plateNumber))
        GPIO.output(6,False)
        time.sleep(gateOpenPeriod)
        GPIO.output(6,True)
    return 'JSON Posted'

app.run(host='0.0.0.0', port= 8010)
atexit.register(lambda: scheduler.shutdown())

