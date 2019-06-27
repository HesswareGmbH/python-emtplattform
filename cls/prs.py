import requests
import json
import urllib
import time
import base64

verify_SSL = False



# Some enums to make it easier to read
# we use python 2.7 so enum.Enum is not available
class CommandMode(object):
	ProgMode = 0
	DataMode = 1
	WaitForAck = 2



class MeterReading(object):
	def __init__(self):
		self.timestamp = -1

class MeteringPoint(object):
	def __init__(self, json, prs):
		self.name = json["name"]
		self.lastRecord = json["unixTstmpLastPushRecords"]
		self.medium = json["medium"]
		self.gatewayOwnerNo = json["gatewayOwnerNo"]
		self.__firstreadingID = -1
		self.__sendInterval = json["sendInterval"]
		self.__prs = prs


	def getReading(self, timestamp):
		return MeterReading()


class Gateway(object):
	def __init__(self, json, prs):
		self.name = json["ownerNo"]
		self.mac = json["macAddress"]

		if not json["lastPing"] is None:
			self.lastPing = json["lastPing"]["gwTimestamp"]
			self.confHash = json["lastPing"]["cnfHash"]
			self.swHash   = json["lastPing"]["swHash"]
		else:
			self.lastPing = 0
			self.confHash = "0000000"
			self.swHash   = "0000000"

		self.created = int(int(json["created"]) / 1000)
		self.onlineControl = False

		self.__prs = prs



class PRS(object):

	"""
		user = username to use
		passwd = password to use
		url = base url for the PRS instance
		cache_time = Data cache in seconds
		api_key = Key to use the API directly
	"""
	def __init__(self, url, user, passwd, cache_time = 60, api_key = "special-key"):
		self.__prs = url
		self.__key = api_key
		self.__meteringPoints = dict()
		self.__meteringPointsLast = 0

		self.__gateways = dict()
		self.__gatewaysLast = 0

		s = requests.Session()
		s.auth = (user, passwd)
		self.__session = s

		self.__headers = {'Accept': 'application/json'}

	def getData(self, module, function):
		url = "%s/%s/%s?api_key=%s" % (self.__prs, module, function, self.__key)
		r = self.__session.get(url, headers=self.__headers, verify=verify_SSL)
		return r

	def postData(self, module, function, data_to_send):
		url = "%s/%s/%s?api_key=%s" % (self.__prs, module, function, self.__key)
		#data_to_send["api_key"] = self.__key
		r = self.__session.post(url, headers=self.__headers, verify=verify_SSL, data = data_to_send)
		return r

	def getMeteringPoints(self):
		error = False
		errorCode = 0

		if time.time() - self.__meteringPointsLast < 60:
			return (self.__meteringPoints, error, errorCode)

		r = self.getData("mds", "meteringpoints")
		try:
			decoded = json.loads(r.text)

			mpoints = dict()

			# We fetch name and last pushRecord here
			for mpoint in decoded:
				mpoints[mpoint["name"]] = MeteringPoint(mpoint, self)

			# Override the current values
			self.__meteringPointsLast = time.time()
			self.__meteringPoints = mpoints

		except ValueError:
			error = True
			errorCode = 1500

		return (self.__meteringPoints, error, errorCode)

	def getGateways(self):
		error = False
		errorCode = 0

		if time.time() - self.__gatewaysLast < 60:
			return (self.__gateways, error, errorCode)

		r = self.getData("mds", "gateways")
		try:
			decoded = json.loads(r.text)

			gateways = dict()

			# We fetch name and last pushRecord here
			for gateway in decoded:
				gateways[gateway["ownerNo"]] = Gateway(gateway, self)

			# Override the current values
			self.__gatewaysLast = time.time()
			self.__gateways = gateways

			self.__updateOnlineGW()

		except ValueError:
			error = True
			errorCode = 1500

		return (self.__gateways, error, errorCode)

	def __updateOnlineGW(self):
		error = False
		errorCode = 0

		retData = dict()

		r = self.getData("smpf-json", "connections/list")
		try:
			decoded = json.loads(r.text)
			onlinegw = list()

			# We need to check for the mac to be right
			for gateway in decoded:
				if (not gateway or not gateway["macAddress"]):
					continue;

				# Wow this is ugly, can someone come up with a better version, please?
				mac = gateway["macAddress"].split(":")
				gwmac = "%s%s%s%s%s%s" % (mac[0].zfill(2),
								mac[1].zfill(2),
								mac[2].zfill(2),
								mac[3].zfill(2),
								mac[4].zfill(2),
								mac[5].zfill(2))
				onlinegw.append(gwmac)

			# Set all gateways to offline
			for gw in self.__gateways:
				if self.__gateways[gw].mac in onlinegw:
					retData[self.__gateways[gw].name] = self.__gateways[gw]
					self.__gateways[gw].onlineControl = True

		except ValueError:
			error = True
			errorCode = 1500

		return (retData, error, errorCode)

	def getOnlineGWs(self):
		return dict()


	def _sendRLMFetchCommand(self, command, mac, owner, start, end):
		error = False
		errorCode = 1500

		params = "{\"owner\":\"%s\",\"start\":%d,\"end\":%d}" % (owner, start, end)
		data = {"mac": mac, "pluginname": "rlm_readout", "plugincall": command, "params": params }

		r = self.postData("smpf-json", "gateways/sendcommand/tomac", data)

		if r.status_code == requests.codes.ok:
			error = True
			errorCode = r.status_code

		return r.text.encode('utf-8'), error, errorCode

	# Short cuts
	def fetchLastgang(self, mac, owner, start, end):
		return self._sendRLMFetchCommand("fetchLastgang", mac, owner, start, end)

	def fetchErrorLog(self, mac, owner, start, end):
		return self._sendRLMFetchCommand("fetchErrorLog", mac, owner, start, end)

	def sendRLMCommand(self, mac, owner, command, prog = 0, timeout = -1):
		error = False
		errorCode = 1500

		params = "{\"owner\":\"%s\",\"command\": \"%s\", \"prog\":%i,\"timeout\":%i}" % (owner, command, prog, timeout)
		data = {"mac": mac, "pluginname": "rlm_readout", "plugincall": "sendCommand" , "params": params }
		r = self.postData("smpf-json", "gateways/sendcommand/tomac", data)

		if r.status_code == requests.codes.ok:
			error = True
			errorCode = r.status_code

		return r.text, error, errorCode

	def getLoadCurve(self, mpoint, start, end):
		error = False
		errorCode = 0

		retData = list()

		r = self.getData("mds", "/meteringpoints/rlm/%s/%d/%d" % (mpoint, start, end))

		try:
			decoded = json.loads(r.text)

			for encoded in decoded:
				retData.append(base64.b64decode(encoded))

		except ValueError:
			error = True
			errorCode = 1500

		return (retData, error, errorCode)

