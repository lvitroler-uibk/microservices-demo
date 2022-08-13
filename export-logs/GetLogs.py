import requests
from requests.structures import CaseInsensitiveDict
import sys
import logging
import os
import datetime

import json

allServices = ["emailservice", "checkoutservice", "recommendationservice", "classifyingservice", "frontend",
                "paymentservice", "productcatalogservice", "cartservice", "shippingservice", "adservice",
                "frontend-external", "currencyservice"]

BASIC_URL = "http://localhost:20001/kiali/api/namespaces/default/"
WORKLOAD_URL = BASIC_URL + 'workloads/'
POD_URL = BASIC_URL + 'pods/'

def callAPI(service):
    try:
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        responseWorkload = requests.get(url=WORKLOAD_URL + service, headers=headers)
        pods = responseWorkload.json()['pods']
        pods[0]['name']

        response = requests.get(url=POD_URL + pods[0]['name'] + '/logs?container=server&tailLines=1000&isProxy=false' , headers=headers)

        if response is None:
            raise ValueError("response is missing")
        else:
            return response.json
    except Exception as e:
        logging.error('Error while getting the data from url', exc_info=e)
        sys.exit()


def write_to_json(jsonFile, filename, services):
    parent_dir = os.getcwd()
    # Directory
    directory = filename + "_" + str(datetime.date.today())
    # Path
    path = os.path.join(parent_dir+"/LOGS", directory)
    try:
        os.makedirs(path)
    except:
        print("Directory already exists")

    with open(path + "/" + filename + "_" + services + ".json", 'w') as file:
        json.dump(jsonFile, file)
        print("TRACES are saved in File: ", filename + "_" + services + ".json")


def mainLogs(filename):
    for service in allServices:
        jsonFile = callAPI(service)
        write_to_json(jsonFile, filename, service)

