import requests
import json
import urllib
import time
import base64
import logging
from .clsmodule import CLSModule 
from .switchingpoint import SwitchingPoint
from .datastore import Datastore

verify_SSL = True

class CLSCenter(object):
  """
    This object includes all functions to get access to the funtions of the CLS Modules
  """

  def __init__(self, url, user, password, tenant, cache_time=60, api_key="special-key"):

    # Store private variables
    self.clscenter = url
    self.key = api_key

    self.clsmodules = dict()

    # Store the Session to use
    s = requests.Session()
    self.session = s

    self.headers = dict()

    # Get authentification token
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    data = {"username": user, "password": password, "tenant": tenant }

    r = requests.post("%s/clscenter/oauth/token" % url, data=data,
                      headers=headers, verify=verify_SSL, allow_redirects=False)

    # We need to store this json
    original_error = r.text

    if r.status_code == 200:
      data = json.loads(r.text)
      self.headers["Authorization"] = "Bearer %s" % data["access_token"]
      logging.debug("OAUTH authentification finished")
    else:
      logging.debug("OAUTH failed, trying old PRS way")

      # This may be an old installation in this case we need to try a different way
      r = self.session.post("%s/clscenter/resources/j_spring_security_check" % url,
                            headers=headers,
                            data={"j_username": user, "j_password": password},
                            verify=verify_SSL,
                            allow_redirects=False)

      if r.status_code == 200 or r.status_code == 301 or r.status_code == 302:
        if not "Set-Cookie" in r.headers:
          logging.debug("Old authentification failed")
          raise Exception

        self.headers["Cookie"] = r.headers["Set-Cookie"]

        logging.debug("Host %s should be upgraded to OAUTH2", url)
      else:
        logging.error("Login not succeeded: %s",original_error)
        raise Exception

    # Some default headers
    self.headers["Accept"] = 'application/json'


  def checkGWOnline(self, mac):
    r = self.getData("clscenter", "connections/list")
    if r.status_code == 200:
      data = json.loads(r.text)
    else:
      raise Exception

    m_list = map(''.join, zip(*[iter(mac)]*2))
    mac = ':'.join(m_list)

    for module in data:
      if module["macAddress"] == mac:
        return True

    return False

  def getModulesOnline(self):
    # Now set the online status depending on the connection list
    r, status_code = self.getData("clscenter", "connections/list")
    if status_code == 200:
      data = json.loads(r.text)
    else:
      logging.error("Unable to get the connection list (http code %d, data: %s)", r.status_code,r.text)
      raise Exception

    print(data)
    modules = {}

    i = 0
    # The id is the same as before so set it
    for module in data:
      modules[i] = {}
      modules[i]["macAddress"] = module
      modules[i]["online"] = True
      i = i + 1
    return modules

  def getAllModules(self):
    r = self.getData("clscenter", "gateways")
    if r.status_code == 200:
      data = json.loads(r.text)
    else:
      logging.error("Failed to get gateways (http code %d, data: %s)", r.status_code,r.text)
      raise Exception

    modules = {}
    for module in data:
      if not "macAddress" in module:
        continue

    m = CLSModule(module["macAddress"], self)
    m.setOwnerID(module["ownerNo"])
    modules[int(module["id"])] = m

    # Now set the online status depending on the connection list
    r = self.getData("clscenter", "connections/list")
    if r.status_code == 200:
      data = json.loads(r.text)
    else:
      logging.error("Unable to get the connection list (http code %d, data: %s)", r.status_code,r.text)
      raise Exception

    # The id is the same as before so set it
    for module in data:
      modules[int(module["id"])].online = True

    return modules


  def getAllSwitchingPoints(self):
    r = self.getData("clscenter", "switchingpoints")
    if r.status_code == 200:
      data = json.loads(r.text)
    else:
      raise Exception

    swpoints = {}

    for module in data:
      if not "gateway" in module or module["gateway"] is None:
        logging.debug("Bad module on host %s: %s", self.clscenter, module)
        continue

      s = SwitchingPoint(center=self,
                         switchingPoint=module["name"],
                         id=module["id"],
                         gw_id=module["gateway"]["id"],
                         controlType=module["controlType"],
                         valueSet=module["valueSet"])

      swpoints[int(module["id"])] = s

      return swpoints

  def getModule(self, mac):
    return CLSModule(mac, self)

  def getSwitchingPoint(self, switchingPoint):
    return SwitchingPoint(switchingPoint, self)

  def getDatastore(self):
    return Datastore(self)

  def getData(self, module, function):
    url = "%s/%s/%s?api_key=%s" % (self.clscenter, module, function, self.key)
    r = self.session.get(url, headers=self.headers, verify=verify_SSL, allow_redirects=False)
    return r, r.status_code

  def postData(self, module, function, data_to_send):
    url = "%s/%s/%s?api_key=%s" % (self.clscenter, module, function, self.key)
    r = self.session.post(url, headers=self.headers, verify=verify_SSL, data=data_to_send, allow_redirects=False)
    return r, r.status_code

  def putData(self, module, function, data_to_send):
    url = "%s/%s/%s?api_key=%s" % (self.clscenter, module, function, self.key)
    r = self.session.put(url, headers=self.headers, verify=verify_SSL, data=data_to_send, allow_redirects=False)
    return r, r.status_code

  def getJsonData(self, module, function):
    header_code = 200
    json = ""

    r = self.getData(module, function)
    try:
      json = r.json()
      header_code = r.status_code
    except ValueError:
      return (dict(), 500)

    return (json, header_code)

  def putJsonData(self, module, function, data):
    header_code = 200
    json = ""

    r = self.putData(module, function, data)
    try:
      json = r.json()
      header_code = r.status_code
    except ValueError:
      return (dict(), 500)

    return (json, header_code)

  def postJsonData(self, module, function, data):
    header_code = 500
    json = ""

    url = "%s/%s/%s?api_key=%s" % (self.clscenter, module, function, self.key)
    r = self.session.post(url, headers=self.headers, verify=verify_SSL, data=data)

    header_code = r.status_code

    try:
      json = r.json()
      header_code = r.status_code
    except ValueError:
      pass

    return (json, header_code)


  # New spring checks for content type differently
  def postJsonData2(self, module, function, data):
    header_code = 500
    json = ""

    headers = self.headers
    headers["Content-Type"] = "application/json"

    url = "%s/%s/%s?api_key=%s" % (self.clscenter, module, function, self.key)
    r = self.session.post(url, headers=headers, verify=verify_SSL, data=data)

    try:
      json = r.json()
      header_code = r.status_code
    except ValueError:
      pass

    return (json, header_code)

  def convertMac(self, mac):
    new_mac = mac
    if not ':' in mac:
      new_mac = ""
      if mac[0:1] != "0":
        new_mac = new_mac + mac[0:1]

      new_mac = new_mac + mac[1:2]
      # The new mac format does not use dots
      for i in range(2, len(mac), 2):
        offset = 0
        if (mac[i] == "0"):
          offset = 1
        new_mac = new_mac + ":"  + mac[i+offset:i+2]

    return new_mac

