import datetime
import os
import re
import sys
from datetime import date

import requests
from requests.structures import CaseInsensitiveDict
import json
import csv

#URL_SHORT = "https://console.apps.play.gepaplexx.com/api/prometheus" #TODO funktioniert mit der nicht

URL_SHORT = "https://prometheus-k8s-openshift-monitoring.apps.play.gepaplexx.com"  # ?service=ts-auth-service&prettyPrint=true" #traces für einen Service
#URL = "https://prometheus-k8s-openshift-monitoring.apps.play.gepaplexx.com/api/v1/query?query=up[1m]"
AUTHORIZATION = "Bearer sha256~BhFivk7wCVvTgXPbw_6v9CwrWz9_YpDfvQr9EHSF-IY"

'''
    collect monitoring data from specific metric
'''
def callAPI(metrixName):
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers[
        "Authorization"] = AUTHORIZATION  # Token deines Openshift Users verwenden (In Openshift rechts oben auf deinen Usernamen klicken -> Copy login command -> Display Token -> dann den Token nach --token= kopieren und einfügen)

    response = requests.get('{0}/api/v1/query'.format(URL_SHORT), headers=headers, params={'query': metrixName+'[1h]'})
    return response.json()

'''
    Identify all potential metric names collected by Prometheus
'''
def GetMetrixNames():
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers[
        "Authorization"] = AUTHORIZATION
    response = requests.get('{0}/api/v1/label/__name__/values'.format(URL_SHORT), headers=headers)
    names = response.json()['data']    #Return metrix names
    return names


def write_to_json(jsonFile, filename, metric):
    parent_dir = os.getcwd()
    # Directory
    directory = "Monitoring_" + filename + "_" + str(datetime.date.today())
    # Path
    path = os.path.join(parent_dir+"/RESULTS", directory)
    try:
        os.makedirs(path)
    except:
        print("Directory already exists")
    re.sub(r'[^a-zA-Z]', '_', metric)
    print(metric)
    with open(path + "/" + filename + "_" + metric + ".json", 'w') as file:
        json.dump(jsonFile, file)
        print("MONITORING are saved in File: ", filename + "_" + metric + ".json")

#def write_to_json(jsonFile, filename):
#    with open("RESULTS/" + filename, 'w') as file:
#        for listelements in jsonFile:
#            json.dump(listelements, file)
#        print("Monitoring Data saved in File: ", filename)


'''
    identify all potential metric names and loop through them to collect all monitoring data
'''
def mainMonitoringData(filename):
    metrixNames = GetMetrixNames()
    for metrixName in metrixNames:
        jsonFile = callAPI(metrixName)
        write_to_json(jsonFile, filename, metrixName)




