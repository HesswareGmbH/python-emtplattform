import requests
import json
import logging

verify_SSL = True

class Statistics(object):
  """
    This object includes functions to access the statistics module
  """
  def __init__(self, center=None):
    self.center = center

  def lastonoff(self, mac):
    # https://one.bmz.cloud/statistics/statisticevents/70B3D57AFA66/lastonoff
    (json, header_status) = self.center.getJsonData("statistics","statisticevents/%s/lastonoff" % mac)
    if header_status != 200:
       logging.error("Could not execute call to lastonoff")
       return None

    if json["replyCode"] != 200:
       logging.error("Could not execute lastonoff cause: " + json["replyText"])
       return None

    return json["data"]

  def getStatisticEvents(self, mac, ts_start, ts_end):
    # https://one.bmz.cloud/statistics/statisticevents/70B3D57AFA66/1563786435388/1563793635388
    # The times are milliseconds
    ts_start = int(ts_start * 1000)
    ts_end = int(ts_end * 1000)
    (json, header_status) = self.center.getJsonData("statistics","statisticevents/%s/%d/%d" % (mac, ts_start, ts_end))

    if header_status != 200:
       logging.error("Could not execute get statistic events")
       return None

    if json["replyCode"] != 200:
       logging.error("Could not execute events cause: " + json["replyText"])
       return None

    return json["data"]


