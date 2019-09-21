#!/usr/bin/env python3
import argparse
import sys
import logging
import json
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
    parser.add_argument("-ts", "--timestampStart", dest="startTimestamp", help="timestamp start",
                        type=int, required=True)
    parser.add_argument("-te", "--timestampEnd", dest="endTimestamp", help="timestamp end",
                        type=int, required=True)
    parser.add_argument("-o", "--fileOut", dest="fileOutput", help="write result into file", default=True)


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

    aggregate = '[{"$match": {"data.ownernumber":"' + args.sensorId + '", "ts.datastore" : {"$gte": ' + args.startTimestamp + ', "$lte": ' + args.endTimestamp + ' }}},{"$sort":{"ts.datastore":1}}, {"$project": {"_id": 0, "_class": 0, "ts.expiresOn": 0}}  ]'
    logging.info("used aggregate: " + aggregate)

    result = datastore.aggregate(aggregate)

    if result is not None:
        prettyResult = json.dumps(result, indent=4, sort_keys=True)
        logging.info(prettyResult)

        if args.fileOutput == True:
            filename = "sensor_" + args.sensorId + ".json"
            f = open(filename, "w")
            f.write(prettyResult)


    sys.exit(0)

