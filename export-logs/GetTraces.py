import datetime
import os
from datetime import date

import requests
from requests.structures import CaseInsensitiveDict
import json
import csv

#list of all available microservices - necessary to query each
allServices = ["ts-admin-basic-info-service", "ts-admin-order-service", "ts-admin-route-service",
               "ts-admin-travel-service", "ts-admin-user-service", "ts-assurance-service", "ts-auth-service",
               "ts-basic-service", "ts-cancel-service", "ts-config-service", "ts-consign-price-service",
               "ts-consign-service", "ts-contacts-service", "ts-execute-service", "ts-food-map-service",
               "ts-food-service", "ts-inside-payment-service", "ts-news-service", "ts-notification-service",
               "ts-order-other-service", "ts-order-service", "ts-payment-service", "ts-preserve-other-service",
               "ts-preserve-service", "ts-price-service", "ts-rebook-service", "ts-route-plan-service",
               "ts-route-service", "ts-seat-service", "ts-security-service", "ts-station-service",
               "ts-ticketinfo-service", "ts-ticket-office-service", "ts-train-service", "ts-travel2-service",
               "ts-travel-plan-service", "ts-travel-service", "ts-user-service", "ts-verification-code-service",
               "ts-voucher-service"]
URL = "http://jaeger-contest-contest.apps.play.gepaplexx.com/api/traces?service="  # ?service=ts-auth-service&prettyPrint=true" #traces für einen Service

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

