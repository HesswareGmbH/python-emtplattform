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
  parser.add_argument("-i", "--imme", dest="imme", help="send immediately", default=False,
                      required=False)
  parser.add_argument("-p", "--payload", dest="payload", help="hex encoded payload to send",
                      required=True)


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
  payload = {}
  payload["imme"] = args.imme
  payload["devEUI"] = args.sensorId
  payload["data"] = args.payload
  payload["port"] = 10


  # ({'data': {'id': '0018B20000002445_c15ca4ff-4ea1-4e3d-8c77-eb3e9a219829', 'imme': False, 'confirmed': False, 'devEUI': '0018B20000002445', 'data': '3132333435', 'port': 1, 'retriesLeft': 0}, 'replyText': 'data', 'replyCode': 200}, 200)

  r, header_code = clscenter.postJsonData2("lnsadapter", "downpackets", json.dumps(payload))
  if header_code != 200:
    logging.critical("Failed to send downlink")
    exit(30)

  if not "replyCode" in r or not "data" in r:
    logging.critical("Response is invalid")
    exit(40)

  if r["replyCode"] != 200:
    logging.critical("There was an error: %s" % r["replyText"])
    exit(50)

  logging.info("The following data was received:")
  logging.info(json.dumps(r["data"], indent=4, sort_keys=True))
  sys.exit(0)

