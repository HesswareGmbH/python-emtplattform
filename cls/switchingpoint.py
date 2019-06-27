from .clsmodule import CLSModule
from .clsexceptions import *

import logging
import requests


class SwitchingPoint(object):

  def __init__(self, switchingPoint, center=None, id=-1, gw_id=-1, controlType=None,
               valueSet=-1):
    self.center = center
    self.swpoint = switchingPoint
    self.id = id
    self.gw_id = gw_id
    self.controlType = controlType
    self.valueSet = valueSet

  def switch(self, value):
    (json, header_code) = self.center.putJsonData("clscenter",
                                      "switchingpoints/byname/%s/%d" % (self.swpoint, value), "")

    if header_code != requests.codes.ok:
      if len(json) == 0 or not "replyCode" in json:
        logging.debug("Got http-status %d but no json object or replayCode", header_code)
        raise CLSInternalError()

      if int(json["replyCode"]) == 409:
        logging.debug("A switching action is already running for swpoint %s", self.swpoint)
        raise CLSActionIsRunning()


    # We got 200 and succeded
    if not "valueApplied" in json:
      logging.debug("Server answer could not be understood: %s", str(json))
      raise CLSUnknownAnswer()

    # We should return the adjusted value here
    value = int(json["valueApplied"])

    logging.debug("Switch succeded")

    # Return the requested value
    return value

