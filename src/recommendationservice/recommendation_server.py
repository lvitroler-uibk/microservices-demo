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

import os
import random
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

import pandas as pd
import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from logger import getJSONLogger
logger = getJSONLogger('recommendationservice-server')

# Start Machine learning methods
def clean_data(x):
    if isinstance(x, list):
        return [str.lower(i.replace(" ", "")) for i in x]
    else:
        #Check if director exists. If not, return empty string
        if isinstance(x, str):
            return str.lower(x.replace(" ", ""))
        else:
            return ''

def create_soup(x):
    return ' '.join(x[const])

def get_recommendations(title, cosine_sim):
    # Get the index of the movie that matches the title
    idx = indices[title]

    # Get the pairwsie similarity scores of all movies with that movie
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort the movies based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    #print(sim_scores)

    # Get the scores of the 4 most similar movies
    sim_scores = sim_scores[1:5]
    # Get the movie indices
    movie_indices = [i[0] for i in sim_scores if i[1] > 0]

    # Return the top 4 most similar movies
    return metadata['id'].iloc[movie_indices]
# End Machine learning methods

# Content-Based Recommender
# https://www.datacamp.com/tutorial/recommender-systems-python
const = 'categories'

f = open ('products.json', "r")
data = json.loads(f.read())
f.close()

data_new = data['products']
metadata = pd.json_normalize(data_new)

metadata[const] = metadata[const].apply(clean_data)
metadata['soup'] = metadata.apply(create_soup, axis=1)

count = CountVectorizer(stop_words='english')
count_matrix = count.fit_transform(metadata['soup'])
cosine_sim2 = cosine_similarity(count_matrix, count_matrix)
metadata = metadata.reset_index()
indices = pd.Series(metadata.index, index=metadata['id'])


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
        googlecloudprofiler.start(service='recommendation_server', service_version='1.0.0', verbose=0, project_id=project_id)
      else:
        googlecloudprofiler.start(service='recommendation_server', service_version='1.0.0', verbose=0)
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

class RecommendationService(demo_pb2_grpc.RecommendationServiceServicer):
    def ListRecommendations(self, request, context):
        productIds = request.product_ids
        logger.info("[Recv ListRecommendations] request_ids={}".format(productIds))

        productId = productIds[0]

        # fetch list of products from product catalog stub
        #cat_response = product_catalog_stub.ListProducts(demo_pb2.Empty())
        #product_ids = [x.id for x in cat_response.products]
        #filtered_products = list(set(product_ids) - set(request.product_ids))
        # sort the list by id
        #filtered_products = sorted(filtered_products)

        #num_products = len(filtered_products)
        #num_return = min(max_responses, num_products)

        # sample list of indicies to return
        #indices = random.sample(range(num_products), num_return)
        #indices = filtered_products[:num_return]
        
        # fetch product ids from indices
        #prod_list = [filtered_products[i] for i in indices]
        result = get_recommendations(productId, cosine_sim2)
        prod_list = result.values

        logger.info("[Recv ListRecommendations] recommended_ids={}".format(prod_list))
        
        # build and return response
        response = demo_pb2.ListRecommendationsResponse()
        response.product_ids.extend(prod_list)
        return response

    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING)

    def Watch(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.UNIMPLEMENTED)


if __name__ == "__main__":
    logger.info("initializing recommendationservice")

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
              module='recommendationserver',
              version='1.0.0'
          )
        except (Exception, DefaultCredentialsError):
            logger.error("Could not enable debugger")
            logger.error(traceback.print_exc())
            pass
    except (Exception, DefaultCredentialsError):
        logger.info("Debugger disabled.")

    port = os.environ.get('PORT', "8080")
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
    service = RecommendationService()
    demo_pb2_grpc.add_RecommendationServiceServicer_to_server(service, server)
    health_pb2_grpc.add_HealthServicer_to_server(service, server)

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
