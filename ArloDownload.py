#!/usr/bin/python
#
# ArloDownload - A video backup utility for the Netgear Arlo System
#
# Version 2.0
#
# Contributors:
#  Janick Bergeron <janick@bergeron.com>
#  Preston Lee <zettaiyukai@gmail.com>
#  Tobias Himstedt <himstedt@gmail.com>
#
# Requirements:
#  Python 3
#  Dropbox Python SDK
#
# This script is open-source; please use and distribute as you wish.
# There are no warranties; please use at your own risk.
#
# Master GIT repository: git@github.com:janick/ArloDownload.git
#

import configparser
import datetime
import dropbox
import json
import os
import pickle
import psutil
import requests
import shutil
import sys


config = configparser.ConfigParser()
config.read('/etc/systemd/arlo.conf')

rootdir = config['Default']['rootdir']
if not os.path.exists(rootdir):
    os.makedirs(rootdir)

# Check if another instance is already running
lock = os.path.join(rootdir, "ArloDownload.pid")
if os.path.isfile(lock):
    pid = int(open(lock, 'r').read())
    if pid == 0:
        print(lock + " file exists but connot be read. Assuming an instance is already running. Exiting.")
        sys.exit
        
    if psutil.pid_exists(pid):
        print("An instance is already running. Exiting.")
        sys.exit()

# I guess something crashed. Let's go ahead and claim this run!
open(lock, 'w').write(str(os.getpid()))
            
# Load the files we have already backed up
dbname = os.path.join(rootdir, "saved.db")
saved = {}
if os.path.isfile(dbname):
    try:
        saved = pickle.load(open(dbname, "rb"))
    except:
        # File was corrupted. Worst that is going to happen is we'll re-fetch everything.
        # Oh well...
        pass

# Should really use backend object, one for local file, one for dropbox
if 'token' in config['dropbox.com']:
    backend = dropbox.Dropbox(config['dropbox.com']['token'])
    print("Dropbox login!")

    
class arlo_helper:
    def __init__(self):
        # Define your Arlo credentials.
        self.loginData = {"email":config['arlo.netgear.com']['userid'], "password":config['arlo.netgear.com']['password']}
        # Define root directory for downloads.
        self.downloadRoot = rootdir
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
        print("Arlo login!")
        self.token = jsonResponseData['token']
        self.deviceID = jsonResponseData['serialNumber']
        self.userID = jsonResponseData['userId']
        self.headers['Authorization'] = self.token

    def readLibrary(self):
        self.today = datetime.date.today()
        now = self.today.strftime("%Y%m%d")
        # A 7-day window ought to be enough to catch everything!
        then = (self.today - datetime.timedelta(days=7)).strftime("%Y%m%d")
        params = {"dateFrom":then, "dateTo":now}
        response = self.session.post(self.libraryUrl, data=json.dumps(params), headers=self.headers)
        self.library = response.json()['data']

    def getLibrary(self):
        itemCount = 0;
        for item in self.library:
            url = item['presignedContentUrl']
            camera = str(self.cameras.get(item['deviceId']))
            sec = int(item['name']) / 1000

            date = str(datetime.datetime.fromtimestamp(sec).strftime('%Y-%m-%d'))
            time = str(datetime.datetime.fromtimestamp(sec).strftime('%H:%M:%S'))
            secs = item['mediaDurationSecond']
            directory = os.path.join(self.downloadRoot, date, camera)
            filename = time + "+" + str(secs) + "s.mp4"
            fullname = os.path.join(directory, filename)
            relname  = os.path.join(date, camera, filename)
            
            # Did we already process this item?
            tag = camera + item['name']
            if tag in saved:
                print("We already have processed " +  relname + "! Skipping download.")
            else:
                itemCount = itemCount + 1
                print("Downloading " + relname)
                response = self.session.get(url, stream=True)
                # Should really use polymorphism here...
                if 'token' in config['dropbox.com']:
                    backend.files_upload(response.raw.read(), "/" + relname)
                else:
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    with open(fullname, 'wb') as out_file:
                        shutil.copyfileobj(response.raw, out_file)
                del response

            saved[tag] = self.today
            if itemCount % 25 == 0:
                # Take a snapshot of what we have done so far, in case the script crashes...
                pickle.dump(saved, open(dbname, "wb"))

    def cleanup(self):
        # Remove the entries in the "saved" DB for files that are no longer available on the arlo server
        for tag in saved:
            if saved[tag] != self.today:
                del saved[tag]
                
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

# Save everything we have done so far...
pickle.dump(saved, open(dbname, "wb"))

print('Done!')

os.unlink(lock)
