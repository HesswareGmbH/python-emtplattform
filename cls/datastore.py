import requests
import json
import logging

verify_SSL = True

class Datastore(object):
  """
    This object includes all functions to get access to the funtions of the datastore
  """
  def __init__(self, center=None):
    self.center = center

  def aggregate(self, aggregate):

    (json, header_status) = self.center.postJsonData("datastore","aggregate", aggregate)
    if header_status != 200:
        logging.error("Could not execute aggregate!")
        return None
    if json["replyCode"] != 200:
        logging.error("Could not execute aggregate cause: " + json["replyText"])
        return None

    return json["data"]

