import json
import sys
import os
import logging
from urllib.parse import urlparse

from .clsexceptions import CLSNoLoginInformationFound

class LoginDataHandler:

  def __init__(self, url, json_file = "secrets.json"):

    self._user = None
    self._password = None
    self._tenant = None

    # We need to check for the right to read the file
    if os.access(json_file, os.R_OK) == False:
      logging.info("Configuration file could not be loaded: %s", json_file)
      raise CLSNoLoginInformationFound

    configuration = dict()

    with open(json_file, "r") as f:
      config = f.read()
      # Check for the configuration
      configuration = json.loads(config)

    uri = urlparse(url)
    hostname = uri.hostname

    if hostname == None:
      logging.info("The URI could not be parsed")
      raise CLSNoLoginInformationFound

    if not hostname in configuration:
      logging.info("No login-data found for host %s", hostname)
      raise CLSNoLoginInformationFound

    if "username" not in configuration[hostname] or "password" not in configuration[hostname] or "tenant" not in configuration[hostname]:
      logging.info("Malformed login-data for host %s", hostname)
      raise CLSNoLoginInformationFound

    self._user = configuration[hostname]["username"]
    self._password = configuration[hostname]["password"]
    self._tenant = configuration[hostname]["tenant"]

  def getUser(self):
    return self._user

  def getPassword(self):
    return self._password

  def getTenant(self):
    return self._tenant

