
import RPi.GPIO as GPIO
import time
import csv
import requests
import coloredlogs, logging
import os, sys
from flask import Flask
from flask import request
import json
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

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

accessListCSV = os.path.join(sys.path[0], 'configDir/accessList.csv')
configLocation = os.path.join(sys.path[0], 'configDir/config.ini')
logLocation = os.path.join(sys.path[0], 'configDir/ppLog.log')

logging.basicConfig(filename=logLocation,format="%(asctime)s:%(levelname)s:%(message)s", filemode='w')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.info("Parkpow Server Started")
print("Parkpow Server Started")

#------------------------Get Configuration Data---------------------#
configValues = {}
with open (configLocation, "rt") as configFile:
    for configValue in configFile:
        key, value = configValue.split('= ')
        configValues[key] = value

gateOpenPeriod = int(configValues.get('gate-open-period'))
pollFrequency = int(configValues.get('poll-frequency'))
apiToken = configValues.get('pr-api-token')
ppApiToken = configValues.get('pp-api-token')

parkpowUrl = "https://app.parkpow.com/api/v1/vehicles/"
paginatedUrl = "https://app.parkpow.com/api/v1/vehicles/?page={apiPageNumber}"
parkpowToken = 'Token {token}'.format(token = ppApiToken.replace('\n', ''))
parkpowHeaders = {}
parkpowHeaders['Authorization'] = parkpowToken
#-------------------------------------------------------------------#
#--------Regularly called to update plate access list---------------#
def updateAccessList():
    GPIO.output(13, True)    

    try:
        ppCurlResponse = requests.get(parkpowUrl, headers=parkpowHeaders)
    except Exception as curlException:
        logger.error('Update Access List Failed: {}'.format(curlException))
        GPIO.output(13, False)
        return
    
    logger.info("Access List Update Start")
    jsonDataCurl = json.loads(ppCurlResponse.content)
    
    #------------Import JSON data into CSV-----------#
    accessList = open(accessListCSV, 'w')
    accessList.close()
    nextPage = 0
    while(nextPage is not None): 
        ppCurlResponse = requests.get(paginatedUrl.format(apiPageNumber=nextPage))
        jsonDataCurl = json.loads(ppCurlResponse.content)
        logger.info(jsonDataCurl)
        print(jsonDataCurl)
        nextPage = jsonDataCurl["next"]
        plateList = jsonDataCurl["results"]
        accessList = open(accessListCSV, 'a')
        accessListWriter = csv.writer(accessList)
        for plate in plateList:
            accessListWriter.writerow(plate.values())
        accessList.close()  
    #------------------------------------------------#
    time.sleep(1)
    GPIO.output(13, False)
##------------------------------------------------------------------#

gate1_Cameras = configValues.get('gate1_CameraList').replace(" ", "")
gate1_Cameras = gate1_Cameras.strip("\n \t").split(',')

gate2_Cameras = configValues.get('gate2_CameraList').replace(" ", "")
gate2_Cameras = gate2_Cameras.strip("\n \t").split(',')

gate1_Tags = configValues.get('gate1_Tags').replace(" ", "").strip("\n \t").split(',')
gate2_Tags = configValues.get('gate2_Tags').replace(" ", "").strip("\n \t").split(',')

print(gate1_Cameras)
print(gate2_Cameras)
print(gate1_Tags)
print(gate2_Tags)

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
    cameraId = parsedJson['hook']['id']
    plateNumber = parsedJson['data']['results'][0]['plate']
    csvAsList = list(csv.reader(open(accessListCSV)))
    print(parsedJson)

    for plates in csvAsList:
        if plateNumber in plates:
            tagList = set(plates[8].strip("[]'").split('&'))
            if (set(gate1_Tags).intersection(tagList)) and (cameraId in gate1_Cameras):
                logger.info("Plate Number {} admitted by {} through gate 1".format(plateNumber, cameraId))
                print('GATE 1 ACCESS GRANTED')
                GPIO.output(5,False)
                time.sleep(gateOpenPeriod)
                GPIO.output(5,True)
            elif (set(gate2_Tags).intersection(tagList)) and (cameraId in gate2_Cameras):
                logger.info("Plate Number {} admitted by {} through gate 2".format(plateNumber, cameraId))
                print('GATE 2 ACCESS GRANTED')
                GPIO.output(6,False)
                time.sleep(gateOpenPeriod)
                GPIO.output(6,True)
            else:
                logger.warning("Plate Number {} denied by {}".format(plateNumber, cameraId))
                print('GATE ACCESS DENIED')

    return 'JSON Posted'

app.run(host='0.0.0.0', port= 8010)
atexit.register(lambda: scheduler.shutdown())

