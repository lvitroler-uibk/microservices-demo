import requests
from requests.structures import CaseInsensitiveDict
import sys
import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan


import pandas as pd
import json
import csv

BASIC_URL = "https://elasticsearch-openshift-logging.apps.play.gepaplexx.com"
URL = "https://elasticsearch-openshift-logging.apps.play.gepaplexx.com/app*/_search?size=10000" #TODO if wanted more than 10000 logs - https://kb.objectrocket.com/elasticsearch/elasticsearch-and-scroll-in-python-953
SCROLL_URL="https://elasticsearch-openshift-logging.apps.play.gepaplexx.com/app*/type/_search?scroll=1m"
AUTHORIZATION = "Bearer sha256~BhFivk7wCVvTgXPbw_6v9CwrWz9_YpDfvQr9EHSF-IY"

PARAM_SCROLL = {
    "size": 100,
    "query": {
        "match" : {
            "title" : "elasticsearch_python_test"
        }
    }
}

# defining a params dict for the parameters to be sent to the API
PARAMS = {
        "query": {
            "query_string": {
                "query": "kubernetes.pod_name: ts-*-service-* AND kubernetes.namespace_name: contest AND kubernetes.container_name.raw: ts-*-service"
            }
        },
        "sort":
            [
                {
                    "@timestamp":
                     {
                         "order":"desc",
                         "unmapped_type":"boolean"
                     }
                }
            ],
        "_source": [
                "message"
        ]
    }




'''
    get 10.000 logs based on globally defined URL & Parameters
'''
def callAPI():
    try:
        if URL is None:
            raise ValueError("URL is missing")

        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = AUTHORIZATION #Token deines Openshift Users verwenden (In Openshift rechts oben auf deinen Usernamen klicken -> Copy login command -> Display Token -> dann den Token nach --token= kopieren und einfügen)
        response = requests.get(url=URL, json=PARAMS, headers=headers)
        responseInJson = response.json()
        print("RESPONSE FROM URL", responseInJson)
        if response is None:
            raise ValueError("response is missing")
        else:
            return responseInJson
    except Exception as e:
        logging.error('Error while getting the data from url', exc_info=e)
        sys.exit()



'''
    get message text our of logs in the following format 
    z.b.: 2022-07-06 21:23:25.595  INFO 1 --- [io-11178-exec-2] i.j.internal.reporters.LoggingReporter   : <variable Log message>
'''
def parseJSON(jsonFile):
    listOfMessages = list()
    onlyHit = jsonFile['hits']['hits']
    for eachHit in onlyHit:
        listOfMessages.append(eachHit['_source']['message'])
    return listOfMessages



def write_to_txt(info_list):
    with open('trainTicket_logs.txt', 'w') as file:
        for eachlistelement in info_list:
            file.write(eachlistelement + "\n")
    print("LOGS are saved in File")


''' scrolling manually by hand if more than 10.000 logs necessary
- deprecated due to available API (see function scroll with help)
'''
def scroll_elasticSearch():
    try:
        if SCROLL_URL is None:
            raise ValueError("SCROLL_URL is missing")

        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers[
            "Authorization"] = AUTHORIZATION  # Token deines Openshift Users verwenden (In Openshift rechts oben auf deinen Usernamen klicken -> Copy login command -> Display Token -> dann den Token nach --token= kopieren und einfügen)
        response = requests.post(url=SCROLL_URL, json=PARAM_SCROLL, headers=headers)
        responseInJson = response.json()
        #json.dump(responseInJson)
        scrollID = responseInJson['_scroll_id']
        print("SCROLL ID: ", scrollID)

        print("Scrollsize", len(responseInJson['hits']['hits']))
        if scrollID is None:
            raise ValueError("scrollID is missing")
        else:
            return scrollID

    except Exception as e:
        logging.error('Error while getting the data from scroll_url', exc_info=e)



'''
    ElasticSearch helper funktion scan allows to scroll for more than 10.000 logs and keeps them persistent while reading the logs
    Applicable for versions under under 7 (we use ElasticSearch 6) --> for younger versions deprecated & scroll is recommended (https://www.elastic.co/guide/en/elasticsearch/reference/current/scroll-api.html#scroll-api)  

    Doc: https://elasticsearch-py.readthedocs.io/en/7.x/helpers.html#scan
'''
def scrollwithHelp(filename):
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers[
        "Authorization"] = AUTHORIZATION
    es = Elasticsearch(BASIC_URL, headers=headers)
    with open("RESULTS/" + filename, "w") as file:
        for hit in scan(es, index="app*", query=PARAMS, preserve_order=True, size=10000, clear_scroll=True):
            file.write((hit['_source']['message']) + "\n")
    print("Logs successfully written to file: ", filename)








def mainLogs(filename):
    ## API Call und parsing nicht mehr notwendig weil mit helper function von ElasticSearch gearbeitet
    #print(callAPI())
    #onlyMessagesOfJson = parseJSON(callAPI())
    #write_to_txt(onlyMessagesOfJson)
    #scroll_elasticSearch()
    scrollwithHelp(filename)
