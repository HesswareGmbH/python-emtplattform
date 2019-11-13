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

  if len(args.sensorId) > 8:
    # it's a deveui
    aggregate = '[{"$match": {"data.ownernumber":"'
  else:
    # its a devaddr
    aggregate = '[{"$match": {"data.lora.dev_addr":"'


  aggregate = aggregate + args.sensorId + '", "ts.datastore" : {"$gte": ' + str(startTimestamp) + ', "$lte": ' + str(endTimestamp) + ' }}},{"$sort":{"ts.datastore":-1}}, {"$project": {"_id": 0, "_class": 0, "ts.expiresOn": 0, "data.obis": 0, "data.unmapped":0}}  ]'

  results = datastore.aggregate(aggregate)
  
  logging.info("Last data from sensor %s:" % args.sensorId)

  if results is None:
    logging.info("No data found for this query")
    sys.exit(2)

 

  table = PrettyTable()
  table.field_names = ["Time", "Gateway", "DevAddr", "Frametype", "Port", "Freq", "SF", "RSSI", "SNR", "FCounter", "FCTRL", "Payload"] 
  
  for result in results:

    if not "data" in result:
      logging.debug("We are missing a data object")
      continue

    if not "mtype" in result["data"]["lora"]:
      logging.debug("No mtype in this frame")
      continue

    timestring = datetime.datetime.fromtimestamp(result["ts"]["datastore"]).strftime('%Y-%m-%d %H:%M:%S')
   
    frame_type = result["data"]["lora"]["mtype"]

    if frame_type == "unconfirmed_data_down":
      frame_type = "UDOWN"
      if (not "decrypted" in result["data"]["raw"] or len(result["data"]["raw"]["decrypted"]) == 0) and result["data"]["lora"]["fctrl"]["ack"] == True:
        frame_type = "ACK ";
    elif frame_type == "confirmed_data_down":
      frame_type = "CDOWN"
    elif frame_type == "unconfirmed_data_up":
      frame_type = "UUP "
    elif frame_type == "confirmed_data_up":
      frame_type = "CUP "
    elif frame_type == "join_request":
      frame_type = "JOIN"
    elif frame_type == "join_accept":
      frame_type = "JACC"

    
    payload = "no data"
    if "decrypted" in result["data"]["raw"]:
      payload = base64.b64decode(result["data"]["raw"]["decrypted"]).hex()
    elif "encrypted" in result["data"]["raw"]:
      payload = "(enc)" + base64.b64decode(result["data"]["raw"]["encrypted"]).hex()

    clsbox = result["clsbox"]
    frame_header = ""

    if "fctrl" in result["data"]["lora"]:
      frame_header = json.dumps(result["data"]["lora"]["fctrl"])

    snr = ""
    rssi = ""

    if "rssi" in result["data"]:
      rssi = str(result["data"]["rssi"])

    if "lsnr" in result["data"]["lora"]:
      snr = str(result["data"]["lora"]["lsnr"])


    fport = "-"
    if "fport" in result["data"]["lora"]:
      fport = result["data"]["lora"]["fport"]

    fcounter = ""
    if "frame_counter" in result["data"]["lora"]:
      fcounter = result["data"]["lora"]["frame_counter"]


    freq = ""
    if "freq" in result["data"]["lora"]:
      freq = result["data"]["lora"]["freq"] / 1000 / 1000

    sf = ""
    if "datr" in result["data"]["lora"]:
      sf = result["data"]["lora"]["datr"]

    devaddr = ""
    if "dev_addr" in result["data"]["lora"]:
      devaddr = result["data"]["lora"]["dev_addr"]

    table.add_row([timestring, clsbox, devaddr, frame_type, fport, freq, sf, rssi, snr, fcounter, frame_header, payload])
    #logging.info("%s\t%s\t%s %s\t%s", timestring, clsbox, frame_type, frame_header, payload)

  print(table)
  sys.exit(0)

