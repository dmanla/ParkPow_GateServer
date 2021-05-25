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

#---Regularly called to update plate access list-------#
def updateAccessList():
    GPIO.output(13, True)    

    try:
        ppCurlResponse = requests.get(parkpowUrl, headers=parkpowHeaders)
    except Exception as curlException:
        logger.error('Update Access List Failed: {}'.format(curlException))
        GPIO.output(13, False)
        return

    jsonDataCurl = json.loads(ppCurlResponse.content)
    plateResults = jsonDataCurl["results"]
    
    #------------Import JSON data into CSV-----------#
    accessList = open(accessListCSV, 'w')
    accessListWriter = csv.writer(accessList)
    counter = 0
    for plate in plateResults:
        if counter == 0:
            header = plate.keys()
            accessListWriter.writerow(header)
            counter += 1
        accessListWriter.writerow(plate.values())
    accessList.close()
    #-=----------------------------------------------#

    time.sleep(2)
    GPIO.output(13, False)
##------------------------------------------------------------------#
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
parkpowToken = 'Token {token}'.format(token = ppApiToken.replace('\n', ''))
parkpowHeaders = {}
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

    cameraId = parsedJson['hook']['id']
    plateNumber = parsedJson['data']['results'][0]['plate']
    csvAsList = list(csv.reader(open(accessListCSV)))

    for plates in csvAsList:
        if plateNumber in plates:
            print(plates)
            if 'Good1' in plates[8] and (cameraId == 'camera-1'):
                logger.info("Plate Number {} admitted by {} through gate 1".format(plateNumber, cameraId))
                print('GATE 1 ACCESS GRANTED')
                GPIO.output(5,False)
                time.sleep(gateOpenPeriod)
                GPIO.output(5,True)
            elif 'Good2' in plates[8] and (cameraId == 'camera-2'):
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

