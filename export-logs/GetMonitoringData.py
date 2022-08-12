import datetime
import os
import re

import requests
from requests.structures import CaseInsensitiveDict
import json

URL_SHORT = "http://localhost:9090"

'''
    collect monitoring data from specific metric
'''
def callAPI(metrixName):
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    response = requests.get('{0}/api/v1/query'.format(URL_SHORT), headers=headers, params={'query': metrixName+'[1h]'})
    return response.json()

'''
    Identify all potential metric names collected by Prometheus
'''
def GetMetrixNames():
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
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

'''
    identify all potential metric names and loop through them to collect all monitoring data
'''
def mainMonitoringData(filename):
    metrixNames = GetMetrixNames()
    for metrixName in metrixNames:
        jsonFile = callAPI(metrixName)
        write_to_json(jsonFile, filename, metrixName)




