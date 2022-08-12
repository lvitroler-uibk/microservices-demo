import datetime
import os
from datetime import date

import requests
from requests.structures import CaseInsensitiveDict
import json

#list of all available microservices - necessary to query each
allServices = ["emailservice", "checkoutservice", "recommendationservice", "classifyingservice", "frontend",
                "paymentservice", "productcatalogservice", "cartservice", "shippingservice", "adservice",
                "frontend-external", "currencyservice"]
URL = "http://localhost:16686/api/traces?service="  # ?service=ts-auth-service&prettyPrint=true" #traces für einen Service

'''
    call to Jaeger to retrieve tracing data for one specific (micro-)service
'''
def callAPI(services):
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    # headers["Authorization"] = "Bearer sha256~6sFu4cLRR5RiwXugAbGRSIu810biPA2nLuWc6kvIV1o" #Token deines Openshift Users verwenden (In Openshift rechts oben auf deinen Usernamen klicken -> Copy login command -> Display Token -> dann den Token nach --token= kopieren und einfügen)
    URL_new = URL + services
    response = requests.get(url=URL_new)
    return response.json()


def write_to_json(jsonFile, filename, services):
    parent_dir = os.getcwd()
    # Directory
    directory = filename + "_" + str(datetime.date.today())
    # Path
    path = os.path.join(parent_dir+"/RESULTS", directory)
    try:
        os.makedirs(path)
    except:
        print("Directory already exists")

    with open(path + "/" + filename + "_" + services + ".json", 'w') as file:
        json.dump(jsonFile, file)
        print("TRACES are saved in File: ", filename + "_" + services + ".json")


def printallservices():
    for service in allServices:
        print(service)
    print(len(allServices))


def mainTraces(filename: object) -> object:
    for services in allServices:
        jsonFile = callAPI(services)
        write_to_json(jsonFile, filename, services)

