#!/usr/bin/env python3
import argparse
import sys
import logging
import datetime
import time
import json
from cls.cls import CLSCenter
from cls.clsmodule import CLSModule
from cls.logindatahandler import LoginDataHandler
from cls.clsexceptions import CLSNoLoginInformationFound
from cls.inventory import Inventory

if __name__ == "__main__":
  # Initialize Logger
  logging.basicConfig()
  logging.getLogger().setLevel(logging.INFO)

  parser = argparse.ArgumentParser()
 
  # generic functions
  parser.add_argument("--debug", dest="generic_debug", action='store_true',
                      help="Enable Debugging", default=False, required=False)
  parser.add_argument("-U", "--url", dest="url", help="URL of the CLS Center",
                      required=True)
  parser.add_argument("-S", "--secrets", dest="secret_file", help="Secret file to use",
                      default="secrets.json", required=False)

  # Script specific functions
  parser.add_argument("-m", "--mac", dest="mac", help="MAC of the gateway",
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
    clsCenter = CLSCenter(args.url, login_data.getUser(),
                          login_data.getPassword(), login_data.getTenant())
  except:
    logging.critical("Login to EMT Instance failed")
    sys.exit(20)


  # The use case specific code follows here
  inventory = Inventory(clsCenter)

  ret = inventory.query("{ \"content.macAddress\": \"%s\" }" % args.mac)

  data = ret[0]
  print("Firmware Version: %s" % data["content"]["versionData"]["baseVersion"])

  print("Original JSON:")
  print(json.dumps(data, sort_keys=True, indent=4))

  # On success use exit code 0
  sys.exit(0)

