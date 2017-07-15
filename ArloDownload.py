#!/usr/bin/python

# arlo_helper - A utility for the Netgear Arlo System
##
# Requirements:
# This script requires the requests-package to be installed, see http://docs.python-requests.org/en/latest/
#
# Developer Notes:
# Developed under Python 3.5
# This script is open-source; please use and distribute as you wish.
# There are no warranties; please use at your own risk.
#
# A very special 'thank you' goes to Tobias Himstedt for the original development of this utility.
# The methods included in this utility were originally written by him and modified for my own usage.
# I am happy to send Tobias' original upon request to my email address.

import configparser
import json
import requests
import datetime
import shutil
import os

author = {'Janick Bergeron', 'janick@bergeron.com'}
version = '2.0'
contributors = {'Tobias Himstedt','himstedt@gmail.com',
                'Preston Lee','zettaiyukai@gmail.com'}

config = configparser.ConfigParser()
config.read('/etc/systemd/arlo.conf')

class arlo_helper:
    def __init__(self):
        # Define your Arlo credentials.
        self.loginData = {"email":config['arlo.netgear.com']['userid'], "password":config['arlo.netgear.com']['password']}
        # Define root directory for downloads.
        self.downloadRoot = config['Default']['rootdir']
        # Cleanup switch; this must be set to "True" in order to use the cleaner module.
        self.enableCleanup = False
        # All directories in format YYYYMMDD, e.g. 20150715, will be removed after x days.
        self.cleanIfOlderThan = 60
        # Define camera common names by serial number.
        self.cameras = {}
        for cameraNum in range (1, 10):
            sectionName = "Camera.{}".format(cameraNum)
            if sectionName in config:
                self.cameras[config[sectionName]['serial']] = config[sectionName]['name']
                
        # No customization of the following should be needed.
        self.loginUrl = "https://arlo.netgear.com/hmsweb/login"
        self.deviceUrl = "https://arlo.netgear.com/hmsweb/users/devices"
        self.metadataUrl = "https://arlo.netgear.com/hmsweb/users/library/metadata"
        self.libraryUrl = "https://arlo.netgear.com/hmsweb/users/library"
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain, application/json'}
        self.session = requests.Session()

    def login(self):
        response = self.session.post(self.loginUrl, data=json.dumps(self.loginData), headers=self.headers )
        jsonResponseData = response.json()['data']
        print("Login success!")
        self.token = jsonResponseData['token']
        self.deviceID = jsonResponseData['serialNumber']
        self.userID = jsonResponseData['userId']
        self.headers['Authorization'] = self.token

    def readLibrary(self):
        self.today = datetime.date.today()
        yesterday = self.today - datetime.timedelta(days=1)
        self.ys = yesterday.strftime("%Y%m%d")
        params = {"dateFrom":self.ys, "dateTo":self.ys}
        response = self.session.post(self.libraryUrl, data=json.dumps(params), headers=self.headers)
        self.library = response.json()['data']

    def getLibrary(self):
        directory = os.path.join(self.downloadRoot, self.ys)
        if not os.path.exists(directory):
            os.makedirs(directory)
        for item in self.library:
            url = item['presignedContentUrl']
            camera = str(self.cameras.get(item['deviceId']))
            sec = int(item['name']) / 1000
            timestamp = str(datetime.datetime.fromtimestamp(sec).strftime('%Y-%m-%d_%H%M%S'))
            filename = os.path.join(directory, camera + "_" + timestamp + ".mp4")
            if os.path.exists(filename):
                print("File " +  filename + " already exists! Skipping download.")
            else:
                print("Downloading " + filename)
                response = self.session.get(url, stream=True)
                with open(filename, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response

    def cleanup(self):
        if not self.enableCleanup:
            return
        older = self.today - datetime.timedelta(days = self.cleanIfOlderThan)
        directoryToCheck = older.strftime("%Y%m%d")
        removeDir = os.path.join(self.downloadRoot,directoryToCheck)
        print("Removing " + removeDir)
        if os.path.exists(removeDir):
            shutil.rmtree(removeDir)

thisHelper = arlo_helper()
thisHelper.login()
thisHelper.readLibrary()
thisHelper.getLibrary()
print('Done!')
