#!/usr/bin/env python3
import argparse
import sys
import logging
import json
import time
import datetime
import base64
from prettytable import PrettyTable
from cls.cls import  CLSCenter
from cls.datastore import Datastore
from cls.logindatahandler import LoginDataHandler
from cls.clsexceptions import CLSNoLoginInformationFound

if __name__ == "__main__":
  # Initialize Logger
  logging.basicConfig()
  logging.getLogger().setLevel(logging.INFO)

  parser = argparse.ArgumentParser()

  # generic functions
  parser.add_argument("--debug", dest="generic_debug", action='store_true',
                      help="Enable Debugging", default=False, required=False)
  parser.add_argument("-U", "--url", dest="url", help="URL of the Datastore",
                      required=True)
  parser.add_argument("-S", "--secrets", dest="secret_file", help="Secret file to use",
                      default="secrets.json", required=False)

  # Script specific functions
  parser.add_argument("-s", "--sensorId", dest="sensorId", help="id of the used sensor",
                      required=True)

  parser.add_argument("-ti", "--timingInterval", dest="timing", help="Hours of data to fetch",
			type=int, required=True)
  args = parser.parse_args()

  # Set the debug level
  if args.generic_debug == True:
    logging.getLogger().setLevel(logging.DEBUG)

  # Get the login data
  try:
    login_data = LoginDataHandler(args.url, args.secret_file)
  except CLSNoLoginInformationFound:
    logging.critical("No login information for this host found")
    sys.exit(10)

  # Try to login
  try:
    clscenter = CLSCenter(args.url, login_data.getUser(),
                          login_data.getPassword(), login_data.getTenant())
  except:
    logging.critical("Login to EMT Instance failed")
    sys.exit(20)

  # The use case specific code follows here

  datastore = clscenter.getDatastore()


  endTimestamp = int(time.time())
  startTimestamp = endTimestamp - (args.timing * 60 * 60)

  aggregate = '[{"$match": { "geo": { "$exists":  true }, "data.ownernumber":"' + args.sensorId + '", "ts.device" : {"$gte": ' + str(startTimestamp) + ', "$lte": ' + str(endTimestamp) + ' }}},{"$sort":{"ts.device":-1}}, {"$project": { "_id": 0, "geo": 1, "data.rssi": 1, "clsbox": 1}}  ]'
  results = datastore.aggregate(aggregate)
  

  if results is None:
    logging.info("No data found for this query")
    sys.exit(2)

 
  geomaps = {}
  geomaps["type"] = "FeatureCollection";
  geomaps["features"] = []

  for result in results:
  
    if not "geo" in result:
      logging.debug("We are missing a geo object")
      continue

    obj = {}

    obj["type"] = "Feature";
    obj["properties"] = {}

    rssi = -256

    if "rssi" in result["data"]:
	    rssi = int(result["data"]["rssi"])

    obj["properties"]["rssi"] = rssi
    obj["properties"]["name"] = args.sensorId
    if (rssi > -100):
      obj["properties"]["marker-color"] = "#B170B1"

    if (rssi > -80):
      obj["properties"]["marker-color"] = "#c7e21e"
 
    if (rssi > -70):
      obj["properties"]["marker-color"] = "#4de307"

    obj["geometry"] = result["geo"]
    geomaps["features"].append(obj)

  print(json.dumps(geomaps, indent=4, sort_keys=True))
  sys.exit(0)

