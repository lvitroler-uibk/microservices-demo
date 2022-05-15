#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function, division
import os
import time
import traceback
from concurrent import futures

import googleclouddebugger
import googlecloudprofiler
from google.auth.exceptions import DefaultCredentialsError
import grpc
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
from opencensus.ext.grpc import server_interceptor
from opencensus.trace import samplers
from opencensus.common.transports.async_ import AsyncTransport

import demo_pb2
import demo_pb2_grpc
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

from PIL import Image
from torchvision import models, transforms
from io import BytesIO

import torch
import torch.nn as nn
import requests
import socket

from logger import getJSONLogger
logger = getJSONLogger('classifyingservice-server')

def initStackdriverProfiling():
  project_id = None
  try:
    project_id = os.environ["GCP_PROJECT_ID"]
  except KeyError:
    # Environment variable not set
    pass

  for retry in range(1,4):
    try:
      if project_id:
        googlecloudprofiler.start(service='classifying_server', service_version='1.0.0', verbose=0, project_id=project_id)
      else:
        googlecloudprofiler.start(service='classifying_server', service_version='1.0.0', verbose=0)
      logger.info("Successfully started Stackdriver Profiler.")
      return
    except (BaseException) as exc:
      logger.info("Unable to start Stackdriver Profiler Python agent. " + str(exc))
      if (retry < 4):
        logger.info("Sleeping %d seconds to retry Stackdriver Profiler agent initialization"%(retry*10))
        time.sleep (1)
      else:
        logger.warning("Could not initialize Stackdriver Profiler after retrying, giving up")
  return

class ClassifyingService(demo_pb2_grpc.ClassifyingServiceServicer):
    def ListClassifyings(self, request, context):
        prod_id = request.product_id
        host = request.host

        # fetch list of products from product catalog stub
        request = demo_pb2.GetProductRequest()
        request.id = prod_id

        product = product_catalog_stub.GetProduct(request)
        #product_ids = [x.id for x in cat_response.products]
        #filtered_products = list(set(product_ids) - set(request.product_ids))
        logger.info("[Recv ListClassifyings] product_id={}".format(prod_id))
        logger.info("[Recv ListClassifyings] host={}".format(host))
        logger.info("[Recv ListClassifyings] picture={}".format(product.picture))

        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logger.info("[Recv ListClassifyings] local={}".format(local_ip))

        # https://www.kaggle.com/code/pavelgot/items-classification-pytorch/notebook
        #response = requests.get("https://static.pullandbear.net/2/photos/2022/V/0/1/p/4246/392/513/4246392513_1_1_3.jpg?t=1646392305779")
        response = requests.get("http://" + host + product.picture)
        img = Image.open(BytesIO(response.content))
        img_t = data_transforms['val'](img).unsqueeze(0)
        img_t = img_t.to(device)
        outputs = model(img_t)
        _, preds = torch.max(outputs, 1)
        predicted = class_names[int(preds.cpu().numpy())]
        logger.info("predicted: {}".format(predicted))

        # build and return response
        response = demo_pb2.ListClassifyingsResponse()
        response.prediction = predicted

        return response

    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING)

    def Watch(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.UNIMPLEMENTED)


if __name__ == "__main__":
    logger.info("initializing classifyingservice")

    try:
      if "DISABLE_PROFILER" in os.environ:
        raise KeyError()
      else:
        logger.info("Profiler enabled.")
        initStackdriverProfiling()
    except KeyError:
        logger.info("Profiler disabled.")

    try:
      if "DISABLE_TRACING" in os.environ:
        raise KeyError()
      else:
        logger.info("Tracing enabled.")
        sampler = samplers.AlwaysOnSampler()
        exporter = stackdriver_exporter.StackdriverExporter(
          project_id=os.environ.get('GCP_PROJECT_ID'),
          transport=AsyncTransport)
        tracer_interceptor = server_interceptor.OpenCensusServerInterceptor(sampler, exporter)
    except (KeyError, DefaultCredentialsError):
        logger.info("Tracing disabled.")
        tracer_interceptor = server_interceptor.OpenCensusServerInterceptor()
    except Exception as e:
        logger.warn(f"Exception on Cloud Trace setup: {traceback.format_exc()}, tracing disabled.") 
        tracer_interceptor = server_interceptor.OpenCensusServerInterceptor()
   
    try:
      if "DISABLE_DEBUGGER" in os.environ:
        raise KeyError()
      else:
        logger.info("Debugger enabled.")
        try:
          googleclouddebugger.enable(
              module='classifyingserver',
              version='1.0.0'
          )
        except (Exception, DefaultCredentialsError):
            logger.error("Could not enable debugger")
            logger.error(traceback.print_exc())
            pass
    except (Exception, DefaultCredentialsError):
        logger.info("Debugger disabled.")

    port = os.environ.get('PORT', "9090")
    catalog_addr = os.environ.get('PRODUCT_CATALOG_SERVICE_ADDR', '')
    if catalog_addr == "":
        raise Exception('PRODUCT_CATALOG_SERVICE_ADDR environment variable not set')
    logger.info("product catalog address: " + catalog_addr)
    channel = grpc.insecure_channel(catalog_addr)
    product_catalog_stub = demo_pb2_grpc.ProductCatalogServiceStub(channel)

    # create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),
                      interceptors=(tracer_interceptor,))

    # add class to gRPC server
    service = ClassifyingService()
    demo_pb2_grpc.add_ClassifyingServiceServicer_to_server(service, server)
    health_pb2_grpc.add_HealthServicer_to_server(service, server)

    # start classifier code
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    class_names = [
        'Backpacks', 
        'Belts', 
        'Bra', 
        'Briefs', 
        'Caps', 
        'Casual Shoes', 
        'Clutches', 
        'Deodorant', 
        'Dresses', 
        'Earrings', 
        'Flats', 
        'Flip Flops', 
        'Formal Shoes', 
        'Handbags', 
        'Heels', 
        'Jackets', 
        'Jeans', 
        'Kurtas', 
        'Lipstick', 
        'Nail Polish', 
        'Perfume and Body Mist', 
        'Sandals', 
        'Sarees', 
        'Shirts', 
        'Shorts', 
        'Socks', 
        'Sports Shoes', 
        'Sunglasses', 
        'Sweaters', 
        'Sweatshirts', 
        'Ties', 
        'Tops', 
        'Track Pants', 
        'Trousers', 
        'Tshirts', 
        'Wallets', 
        'Watches'
        ]
    model_ft = models.resnet18(pretrained=True)
    num_ftrs = model_ft.fc.in_features

    #Changing the number of outputs in the last layer to the number of different item types
    model_ft.fc = nn.Linear(num_ftrs, len(class_names))

    model_ft = model_ft.to(device)
    model = model_ft
    model.load_state_dict(torch.load('model_fine_tuned.pt', device))
    model.eval()

    # Data augmentation and normalization for training
    # Just normalization for validation
    data_transforms = {
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }
    torch.no_grad()
    # end classifier code

    # start server
    logger.info("listening on port: " + port)
    server.add_insecure_port('[::]:'+port)
    server.start()

    # keep alive
    try:
         while True:
            time.sleep(10000)
    except KeyboardInterrupt:
            server.stop(0)
