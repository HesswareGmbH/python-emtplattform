import requests
import json
import logging

verify_SSL = True

class Datastore(object):
  """
    This object includes all functions to get access to the funtions of the datastore
  """

  def __init__(self, url, user, password, tenant, cache_time=60, api_key="special-key"):

    # Store private variables
    self.datastore = url
    self.key = api_key

    # Store the Session to use
    s = requests.Session()
    self.session = s

    self.headers = dict()

    # Get authentification token
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    data = {"username": user, "password": password, "tenant": tenant }

    r = requests.post("%s/datastore/oauth/token" % url, data=data,
                      headers=headers, verify=verify_SSL, allow_redirects=False)

    # We need to store this json
    original_error = r.text

    if r.status_code == 200:
      data = json.loads(r.text)
      self.headers["Authorization"] = "Bearer %s" % data["access_token"]
      logging.debug("OAUTH authentification finished")
    else:
      logging.error("Login not succeeded: %s", original_error)
      raise Exception

    # Some default headers
    self.headers["Accept"] = 'application/json'

  def executeAggregate(self, module, function, aggregate):
    url = "%s/%s/%s" % (self.datastore, module, function)
    logging.debug("used url: " + url)
    r = self.session.post(url, headers=self.headers, verify=verify_SSL, data=aggregate, allow_redirects=False)
    if(r.status_code != 200):
        logging.error("Uneable to execute aggregate cause: " + r.text)
        return
    jsonResponse = json.loads(r.text)
    if(jsonResponse["replyCode"] != 200):
        logging.error(jsonResponse["replyText"])
        return
    return jsonResponse["data"]

