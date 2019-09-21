#!/usr/bin/env python3
import argparse
import sys
import logging
import datetime
import time
from cls.cls import CLSCenter
from cls.clsmodule import CLSModule
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
  parser.add_argument("-U", "--url", dest="url", help="URL of the CLS Center",
                      required=True)
  parser.add_argument("-S", "--secrets", dest="secret_file", help="Secret file to use",
                      default="secrets.json", required=False)

  # Script specific functions
  parser.add_argument("-m", "--mac", dest="mac", help="MAC of the gateway",
                      required=True)
  parser.add_argument("-t", "--hours", dest="hours", help="Number of hours to check for events",
                      default=48, required=False, type=int)
  parser.add_argument("-c", "--count", dest="counts", help="Maximum number of events to print",
                      default=10000, required=False, type=int)

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

  module = clsCenter.getModule(args.mac)

  module.prettyPrint()

  state = module.getLastState()
  ts_end = (int(state["timestamp"]) / 1000)
  ts_start = ts_end - (args.hours * 60 * 60)

  count = 0

  states = module.getStatisticEvents(ts_start, ts_end)

  logging.info("--- Start of event list ---")

  if not states:
    logging.info("API returned None for this query")
  elif len(states) == 0:
    logging.info("No further events logged")
  else:
    for state in states:
      st = datetime.datetime.fromtimestamp(int(state["timestamp"]) / 1000).strftime('%Y-%m-%d %H:%M:%S')
      ss = "Unknown event"
      if state["type"] == "Connect":
        ss = "Module went online"
      elif state["type"] == "Disconnect":
        ss = "Module went offline"
      elif state["type"] == "SwitchOperation":
        ss = "The switchingpoint %s was modified to be %d percent: %s by %s" % (state["switchingPoint"], state["toValue"], state["state"], state["additionalInformation"]["user"])
      elif state["type"] == "PluginCall":
        if state["pluginCall"] == "metersys::sendLoraDownstream":
          ss = "A lora downstream was sent"
        else:
          ss = "The plugin function %s was called" % state["pluginCall"]
      
      logging.info("%s\t%s", st, ss)
      count = count + 1
      if count > args.counts:
        break

  logging.info("--- End of event list ---")

  # On success use exit code 0
  sys.exit(0)

