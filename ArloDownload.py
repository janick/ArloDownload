#!/usr/bin/python

# ArloDownload - An Downloader for Surveillance Videos recorded by the Netgear Arlo System
# Tobias Himstedt, himstedt@gmail.com
#
# This little script logins into the Netgear Arlo Web-Application in order to
# download all videos which were recorded yesterday (resp. the day prior to the current date
# when the script was started)
# This script requires the requests-package to be installed, see http://docs.python-requests.org/en/latest/
# The script was developed using Python 2.7.6. It might run on newer version but it wasn't tested
#
# Do whatever you want with this script
# No warranty, use at your own risk

import json
import requests
import time
import datetime
import shutil
import os

class ArloDownloader:

    def __init__(self):
        # Customize basePath to for the donwload directory
        # Use the following line to download all files to userhome/ArloDownload
        self.basePath = os.path.join( os.path.expanduser("~"), "ArloDownload" )
        # or use any other directory
        # self.basePath = "D:\Arlo"
        # All directories in format YYYYmmdd, e.g. 20150715 will be removed after x days
        self.deleteDownloadsOlderThan = 60 # days
        # Deletion is only done if the following is True
        self.deleteOldStuff = True
        # Important: put in your Arlo credentials in here. Same as if you login on arlo.netgear.com
        self.loginData = {"email":"Arlo_user_email_address", "password":"Arlo_password"}

        # Below this point no customization should be necessary
        self.loginUrl = "https://arlo.netgear.com/hmsweb/login"
        self.deviceUrl = "https://arlo.netgear.com/hmsweb/users/devices"
        self.metadataUrl = "https://arlo.netgear.com/hmsweb/users/library/metadata"
        self.libraryUrl = "https://arlo.netgear.com/hmsweb/users/library"
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain, application/json'}
        self.session = requests.Session()

    def login(self):
        response = self.session.post( self.loginUrl, data=json.dumps(self.loginData), headers=self.headers )
        jsonResponseData = response.json()['data']
        print "Login success"

        self.token = jsonResponseData['token']
        self.deviceId = jsonResponseData['serialNumber']
        self.userId = jsonResponseData['userId']
        self.headers['Authorization'] = self.token

    def getLibrary(self):
        self.today = datetime.date.today()
        yesterday = self.today - datetime.timedelta(days=1)
        self.ys = yesterday.strftime("%Y%m%d")
        params = {"dateFrom":self.ys, "dateTo":self.ys}
        response = self.session.post( self.libraryUrl, data=json.dumps(params), headers=self.headers)
        self.library = response.json()['data']

    def downloadLibray(self):
        directory = os.path.join( self.basePath, self.ys)
        if not os.path.exists(directory):
            os.makedirs(directory)
        for item in self.library:
            url = item['presignedContentUrl']
            name = os.path.join(directory, item['name'] + ".mp4")
            if os.path.exists( name ):
                print "File " +  name + " already exists, skipping download"
            else:
                print "Downloading " + name
                response = self.session.get(url, stream=True)
                with open(name, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response

    def cleanup(self):
        if not self.deleteOldStuff:
            return
        older = self.today -  datetime.timedelta(days = self.deleteDownloadsOlderThan)
        directoryToCheck = older.strftime("%Y%m%d")
        removeDir = os.path.join(self.basePath, directoryToCheck)
        print "Removing " + removeDir
        if os.path.exists( removeDir ):
            shutil.rmtree( removeDir )


ad = ArloDownloader()
ad.login()
ad.getLibrary()
ad.downloadLibray()
ad.cleanup()
