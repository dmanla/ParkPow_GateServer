import RPi.GPIO as GPIO
import time
import csv
import requests
import configparser
import os, sys
from flask import Flask
from flask import request
import json
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

gate_AccessLists = [['sgd6707b'],['sjf5117p']]

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

#---Regularly called to update plate access list-------#
def updateAccessList():
    accessListLocation = os.path.join(sys.path[0], 'configDir/accessList.csv')
    GPIO.output(13, True)    
    
    with open (accessListLocation, "r") as accessListFile:
        gate_AccessLists.clear()
        for accessRecord in accessListFile:
            access1, access2 = accessRecord.split(',')
            gate_AccessLists[0].append(access1)
            gate_AccessLists[1].append(access2.replace("\n", ""))

    time.sleep(2)
    GPIO.output(13, False)
##------------------------------------------------------------------#
#------------------------Get Configuration Data---------------------#
configLocation = os.path.join(sys.path[0], 'configDir/config.ini')
configValues = {}
with open (configLocation, "rt") as configFile:
    for configValue in configFile:
        key, value = configValue.split('= ')
        configValues[key] = value

gateOpenPeriod = int(configValues.get('gate-open-period'))
pollFrequency = int(configValues.get('poll-frequency'))
apiToken = configValues.get('pr-api-token')
ppApiToken = configValues.get('pp-api-token')

parkpowUrl = "https://app.parkpow.com/api/v1/vehicles/
parkpowToken = 'Token {token}'.format(token = ppApiToken.replace('\n', ''))
parkpowHeaders['Authorization'] = parkpowToken

#-------------------------------------------------------------------#
#---Calls "updateAccessList", pollFrequency comes from config.ini---#
scheduler = BackgroundScheduler()
scheduler.add_job(func=updateAccessList, trigger="interval", seconds=pollFrequency)
scheduler.start()
#-------------------------------------------------------------------#
@app.route('/postJson', methods = ['POST'])
def postJsonHandler():
    jsonData = request.form['json']
    parsedJson = json.loads(jsonData)
    plateNumber = parsedJson['data']['results'][0]['plate']

    ppCurlResponse = requests.get(parkpowUrl, headers=parkpowHeaders)
    jsonDataCurl = json.loads(ppCurlResponse.content)
    plateList = [] 
    for plates in jsonDataCurl['results']:
        plateList.append(plates['license_plate'])

    if plateNumber in plateList:
        print("{} permitted through gate".format(plateNumber))
        GPIO.output(5,False)
        time.sleep(gateOpenPeriod)
        GPIO.output(5,True)
    else:
        print("{} denied access".format(plateNumber))
    return 'JSON Posted'

app.run(host='0.0.0.0', port= 8010)
atexit.register(lambda: scheduler.shutdown())

