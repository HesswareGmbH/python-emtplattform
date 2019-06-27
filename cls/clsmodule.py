import json
import requests

class CLSModule(object):

  def __init__(self, mac, center = None):
    self.center = center
    self.mac = mac
    self.online = False
    self.ownerid = ""

  def __str__(self):
    return "CLS-Module: %s" % self.mac

  def getMac(self):
    return self.mac

  def getOwnerID(self):
    return self.ownerid

  def setOwnerID(self, ownerid):
    self.ownerid = ownerid


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

