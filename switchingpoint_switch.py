#!/usr/bin/env python3
import argparse
import sys
import logging
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
  parser.add_argument("-s", "--sw", dest="sw", help="name of the switching point",
                      required=True)
  parser.add_argument("-v", "--value", dest="value", type=int, help="value to set",
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

  sw = clsCenter.getSwitchingPoint(args.sw)
  value_set = sw.switch(args.value)

  if value_set != args.value:
    logging.info("Switching was regulated to %d (we wanted %d)", value_set, args.value)
    # if we do not succeed we need to use exit code > 100
    sys.exit(101)



  logging.info("Switch to %d succeeded", args.value)
  # On success use exit code 0
  sys.exit(0)

