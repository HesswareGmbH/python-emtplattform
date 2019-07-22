import json
from datetime import datetime
import logging
from .statistics import Statistics
from .inventory import Inventory

class CLSModule(object):

  def __init__(self, mac, center = None):
    self.center = center
    self.mac = mac
    self.online = False
    self.ownerid = ""

    inv = Inventory(self.center)
    gw = inv.getGWInfos(self.mac)

    if not gw:
      return None
    if len(gw) == 0:
      return None

    gw = gw[0] # We only need the first element
    self.firmware = gw["content"]["versionData"]["baseVersion"]
    self.ownerid = gw["content"]["ownernumber"]

    # Check our online state
    self.online = center.checkGWOnline(mac)
    

  def __str__(self):
    return "CLS-Module: %s" % self.mac

  def getMac(self):
    return self.mac

  def getOwnerID(self):
    return self.ownerid

  def setOwnerID(self, ownerid):
    self.ownerid = ownerid

  def getLastState(self):
    stats = Statistics(self.center)
    status = stats.lastonoff(self.mac)
    return status

  def getStatisticEvents(self, ts_start, ts_end):
    stats = Statistics(self.center)
    status = stats.getStatisticEvents(self.mac, ts_start, ts_end)
    return status

  def prettyPrint(self):
    logging.info("MAC:        %s", self.mac)
    logging.info("OwnerID:    %s", self.ownerid)
    logging.info("Online:     %s", self.online)
    logging.info("Firmware:   %s", self.firmware)

    state = self.getLastState()
    logging.info("Last Event: %s", state["type"])
    logging.info("Event Time: %s", datetime.fromtimestamp(int(state["timestamp"]) / 1000).strftime('%Y-%m-%d %H:%M:%S'))

    should_be_online = (state["type"] == "Connect")

    if self.online != should_be_online:
      logging.error("** Warning online states do not match, contact support")
    

  def installFirmware(self, update_url):
    payload = {}
    payload["mac"] = self.mac
    payload["pluginname"] = "system"
    payload["plugincall"] = "installFirmware"
    payload["params"] = "{\"firmware_url\":\"%s\"}" % update_url

    (json, header_code) = self.center.postJsonData("clscenter", "gateways/sendcommand/tomac", data=payload)

    # On success we receive an empty body which is different from the other APIs
    if header_code == requests.codes.ok:
      return True

    return False

  def installKernel(self, update_url):

    payload = {}
    payload["mac"] = self.mac
    payload["pluginname"] = "system"
    payload["plugincall"] = "installKernel"
    payload["params"] = "{\"kernel_url\":\"%s\"}" % update_url

    (json, header_code) = self.center.postJsonData("clscenter", "gateways/sendcommand/tomac", data=payload)

    # On success we receive an empty body which is different from the other APIs
    if header_code == requests.codes.ok:
      return True

    return False

  def pluginCall(self, plugin, pluginFunction, pluginData):

    payload = {}
    payload["mac"] = self.mac
    payload["pluginname"] = plugin
    payload["plugincall"] = pluginFunction
    payload["params"] = json.dumps(pluginData)

    (json_data, header_code) = self.center.postJsonData("clscenter", "gateways/sendcommand/tomac", data=payload)
    if header_code == requests.code.ok:
      return True

    return False

