#!/Library/Frameworks/Python.framework/Versions/3.6/bin/ python3

import time, requests, logging
from PIL import Image, ImageDraw, ImageFont

#Image Tweaking Numbers
headerHeightOffset = 2 #distance between header and top of image
fontHeightOffset = 3 #distance between data rows
headerDataOffset = 5 #distance between data and header

class WmataBoard(object):
	"""Initalizes all variables that the virtual board uses"""
	def __init__(self, wmataApiKey, weatherApiKey, latitude, longitude, stationCode, myLines, displayWidth=64, displayHeight=32 ,
		numTrainsToDisplay=3, displayCarData=False, minTrainDistance=5,displayDate=False, dataRefreshRate=3,
		activeTime=True, beginActiveTime=6, endActiveTime=23, displayHeader=False, displayWeather=True, wmataActive=True, displayBasicAlerts=False):

		self.DCMetroHeroApiKey = metroheroApiKey
		self.wmataApiKey = wmataApiKey

		self.wmataActive = wmataActive #This flag means we're using WMATA API info for tracking not metrohero

		self.weatherApiKey = weatherApiKey
		self.latitude = latitude
		self.longitude = longitude

		self.displayWidth = displayWidth
		self.displayHeight = displayHeight
		self.stationCode = stationCode
		self.myLines = myLines
		self.numTrainsToDisplay = numTrainsToDisplay
		self.displayCarData = displayCarData
		self.minTrainDistance = minTrainDistance
		self.upcomingtrains = []
		self.totalNumTrains = 0
		self.displayDate = displayDate
		self.dataRefreshRate = dataRefreshRate
		self.activeTime = activeTime
		self.beginActiveTime = beginActiveTime #in 24 hour time
		self.endActiveTime = endActiveTime #in 24 hour time
		self.lastUpdateTime = 0
		self.lastWeatherUpdateTime = 0
		self.lastFancyAlertDisplayTime = 0 
		self.displayHeader = displayHeader
		self.displayWeather = displayWeather
		self.alertData = []
		self.weatherData = []
		self.displayBasicAlerts = displayBasicAlerts

		self.fancyAlerts = True
		self.readyForFancyAlertScreen = False

		self.refreshData()

	#Method gets the data from the DC Metrohero API, needs to be re-written if you are getting from elsewhere
	def refreshData(self):
		"""Pulls data from the API and stores it interally, then cleans"""
 
		wmataHeaders = {
			 'api_key': self.wmataApiKey
		}

		#make sure we are not refreshing more often than the refresh rate
		if ((time.time() - self.lastUpdateTime) > self.dataRefreshRate):
			rawAlertData = []
			rawTrainData = []
			try:
				#Train data from WMATA
				data = requests.get("https://api.wmata.com/StationPrediction.svc/json/GetPrediction/{}".format(self.stationCode), headers=wmataHeaders)
				rawTrainData = data.json()
				logging.debug("Raw Train Data (JSON): " + str(rawTrainData))

				#Alert data from WMATA
				alerts = requests.get("https://api.wmata.com/Incidents.svc/json/Incidents", headers=wmataHeaders)
				rawAlertData = alerts.json()

				logging.debug("Raw Alert Data (JSON): " + str(rawAlertData))

				self.lastUpdateTime = time.time()

				self.cleanTrainData(rawTrainData)
				self.cleanAlertData(rawAlertData)

			except requests.ConnectionError:
				logging.error("Metro data connection error", exc_info=True)
				time.sleep(10)
				self.refreshData()
			except Exception as e:
				logging.error("Metro Data Error", exc_info=True)

			self.totalNumTrains = len(self.upcomingtrains)

		#weather hard coded to not refresh more than once every 65 mins (3600 seconds)
		if ((time.time() - self.lastWeatherUpdateTime) > 3900) and self.displayWeather:
			try:
				logging.debug("Weather data needs update")
				#Note that imperial units are hardcoded below
				requestWeatherData = requests.get("https://api.weatherbit.io/v2.0/forecast/daily?units=I&lat={}&lon={}&key={}".format(self.latitude, self.longitude, self.weatherApiKey))
				rawWeatherData = requestWeatherData.json()

				logging.debug("Weather data json: " + str(rawWeatherData))

				self.lastWeatherUpdateTime = time.time()
				self.cleanWeatherData(rawWeatherData)

			except requests.ConnectionError:
				time.sleep(300)
				logging.error("Weather data connection error", exc_info=True)
				self.refreshData()
			except Exception as e:
				logging.error('Weather data error', exc_info=True)

	def getTrainData(self):
		"""Returns stored train data"""
		self.refreshData()
		return self.upcomingtrains

	def setTrainData(self, trainData):
		self.upcomingtrains = trainData

	def setAlertData(self, alertDataInput):
		self.alertData = alertDataInput

	#Eventually update this method to handle directionality

	def cleanTrainData(self, trainArray):
		#Loop to handle any special cases (such as Cars being NA) - for efficiency, loop only if showing car data

		trainArray = trainArray["Trains"]

		if self.minTrainDistance > 0:

			newTrainList = [] #for use in below element to clean the train list as we see fit

			for x in trainArray:

				if  self.isInteger(x["Min"]) and int(x["Min"]) >= self.minTrainDistance:
					
					newTrainList.append(x) 

			trainArray = newTrainList

		#only show westbound (1) trains during rush "active time"
		if self.activeTime and (self.beginActiveTime <= time.localtime().tm_hour < self.endActiveTime):

			newTrainList=[]

			for x in range(len(trainArray)):

				if int(trainArray[x]["Group"]) == 1:

					newTrainList.append(trainArray[x])

			trainArray = newTrainList

		logging.debug("cleaned train data :" + str(newTrainList))

		self.setTrainData(trainArray)

	def cleanAlertData(self, rawAlertData):

		if rawAlertData:

			alertArray = rawAlertData["Incidents"]

			newAlertList = []

			for alert in alertArray:

				linesImpacted = [x.strip() for x in alert["LinesAffected"].split(';')]

				if bool(set (linesImpacted) & set (self.myLines)): 

					newAlertList.append(alert["Description"])

			self.alertData = newAlertList
		else:
			self.alertData = rawAlertData

	def cleanWeatherData (self, rawWeatherData):

		if rawWeatherData == []:
			self.weatherData = [] 
			
		self.weatherData = rawWeatherData["data"][0]

	def getWeatherData (self):
		"""Returns weather data"""
		return self.weatherData

	def getDirection(self, trainNum, trains):
		return trains[trainNum]["directionNumber"]

	def getLine(self, trainNum, trains):
		return trains[trainNum]["Line"]

	def getCars(self, trainNum, trains):
		return trains[trainNum]["Car"]

	def isInteger(self, n):
		try:
			answer = int(n)
			return True
		except ValueError:
			return False

	def getDest(self, trainNum, trains):

		###THIS SECTION BELOW WORKS FOR WMATA, OLD STUFF BELOW IS FROM METROHERO DAYS

		if self.wmataActive: 
			return trains[trainNum]["Destination"]


		#Shortened names, if you have preferred output to the full destination name or abbreviations
		namedict = {'Wiehle-Reston East' : "Wiehle",
			'Largo Town Center': "Largo",
			'New Carrollton' : "NCrtn",
			'Vienna/Fairfax-GMU' : "Vienna"}

		metroHeroName = trains[trainNum]["DestinationName"]

		if self.displayCarData or metroHeroName not in namedict :
			 return trains[trainNum]["destinationStationAbbreviation"]
		else:
			return namedict[metroHeroName]

	def getMin(self,trainNum, trains):
		#if we have a minimum distance, we can assume that we're not showing boarding or arriving trains
		# therefore, let's go ahead and convert those outputs to integers for later on
		if self.minTrainDistance > 0:
			if trains[trainNum]["Min"] == "BRD":
				return "-1"
			if trains[trainNum]["Min"] == "ARR":
				return "0"

		return trains[trainNum]["Min"]

	#The below method only works with metrohero!
	def getMinWithSlow(self,trainNum, trains):
		if trains[trainNum]['isCurrentlyHoldingOrSlow']:
			return ("*" + trains[trainNum]["Min"])
		return trains[trainNum]["Min"]

	def getAlertData(self):
		self.refreshData()
		return self.alertData

	# If the car data is being displayed, then destination is shortened to "DST" for display space
	def drawHeader(self,drawObj, font):

		lineWidth = 0
		textHeight = 0

		#use the real draw object if drawing the header
		if self.displayHeader:
			draw = drawObj
		else:
			#fake draw so we don't actually draw on the board if not displaying header
			image = Image.new("RGB", (self.displayWidth, self.displayHeight))
			draw  = ImageDraw.Draw(image)

		headerfont = font
		textHeight = headerfont.getsize("LN")[1]
		lineWidth = headerfont.getsize("LN ")[0]
		minWidth = self.displayWidth - headerfont.getsize("MIN")[0] - 1 #The minus one leaves padding on the right edge

		carWidth = 0 #Set to zero, so that it will remain zero if Car data not being displayed

		draw.text((0,0 - headerHeightOffset), "LN", fill="red", font=headerfont)

		if self.displayCarData:

			carWidth = lineWidth + headerfont.getsize("CR ")[0]

			draw.text((lineWidth,0 - headerHeightOffset), "CR", fill="red", font=headerfont)
			draw.text((carWidth,0 - headerHeightOffset), "DST", fill="red", font=headerfont)
		else:
			draw.text((lineWidth, 0 - headerHeightOffset), "DEST", fill="red", font=headerfont)

		draw.text((minWidth,0 - headerHeightOffset), "MIN", fill="red", font=headerfont)

		return (lineWidth, textHeight)

	def drawTime(self, drawObj, clockFont):

		if self.numTrains < 3:
			draw = drawObj
			font = clockFont

			#how far down on the display are we drawing date/time
			dateTimeHeight = self.displayHeight - font.getsize(time.strftime("%I:%M %p"))[1]

			#At what point in relation to right edge should we draw date
			dateWidth = self.displayWidth - font.getsize(time.strftime("%m/%d"))[0] - 1

			#draw the time
			draw.text((0,dateTimeHeight), time.strftime("%I:%M %p"), fill = "white", font=font)
			#draw the date
			draw.text((dateWidth, dateTimeHeight), time.strftime("%m/%d"), fill = "white", font=font)

	def weatherString(self):
		"""Creates weather string to draw on board"""

		weatherData = self.getWeatherData()

		currentTemp = round(weatherData["temp"])
		highToday = round(weatherData["high_temp"])
		lowToday = round(weatherData["low_temp"])
		precip = round(weatherData["pop"])
		description = weatherData["weather"]["description"]

		outputString = description + "."
		outputString += " Current: " + str(currentTemp) + u"\xb0"
		outputString += " Precp: " + str(precip) + "%"
		outputString += " High: " + str(highToday) + u"\xb0"
		outputString += " Low: " + str(lowToday) + u"\xb0" + " "

		return outputString

	def dataDrawer(self,fontPath):

		image = Image.new("RGB", (self.displayWidth, self.displayHeight)) # Can be larger than matrix if wanted!!
		draw  = ImageDraw.Draw(image)    # Declare Draw instance

		font = ImageFont.load(fontPath) #this is the train data font

		draw.rectangle((0,0,self.displayWidth,self.displayHeight), fill="black") #background of image, black rectangle

		headerValues = self.drawHeader(draw, font) #returns header widths as tuple

		lineWidth = headerValues[0]
		textHeight = headerValues[1]
		carWidth = 0

		#Idea here is to localize the variables and "freeze" it, since there might be a data update in the background
		totalNumTrains = self.totalNumTrains
		trains = self.upcomingtrains

		self.numTrains = 0 #by default, we assume no trains are coming

		#want to display max of however many trains set in initalization
		if totalNumTrains > (self.numTrainsToDisplay-1):
			self.numTrains = self.numTrainsToDisplay
		else:
			self.numTrains = totalNumTrains

		#Loop to handle car data being "NA" which is surprisingly often
		if self.displayCarData:
			for x in range(self.numTrains):
				carNum = self.getCars(x,trains)
				if carWidth < (font.getsize(carNum)[0] + 2):
					carWidth = font.getsize(carNum)[0] + 2
		else:
			lineWidth = lineWidth + 1 #if we're not showing the car data, let's add some space since we have it

		#LOOP FOR EACH DRAWING EACH TRAIN'S DATA
		for x in range(self.numTrains):

			#If we are showing the header, then the car data should start one line down. otherwise at top.
			if self.displayHeader:
				lineHeight = textHeight + textHeight*x #move the cursor down as we fill in data
			else:
				lineHeight = 3 + textHeight*x #Add 3 so it's not cut off, then moves cursor down.

			#Probably a more elegant way to do it, but below line moves the cursor back up a little bit,
			# depending on offset values, to reduce empty space
			lineHeight = lineHeight - fontHeightOffset*x - headerDataOffset

			if self.getLine(x, trains) == "OR":
				draw.text((0,lineHeight), self.getLine(x, trains), fill="orange", font=font) #fill OR LINE data
			elif self.getLine(x, trains) == "SV":
				draw.text((0,lineHeight), self.getLine(x, trains), fill="silver", font=font) #fill SV LINE data
			else:
				#fill colors besides orange & silver lines as yellow
				draw.text((0,lineHeight), self.getLine(x, trains), fill="yellow", font=font)

			#draw car data, if we're displaying it
			if self.displayCarData:
				carNum = self.getCars(x, trains)
				#print 8 car trains as green, just like the real boards do
				if carNum == '8':
					draw.text((lineWidth + 1, lineHeight), carNum, fill="green", font=font) #fill destination
				else:
					draw.text((lineWidth + 1, lineHeight), carNum, fill="yellow", font=font) #fill destination

			draw.text((lineWidth + carWidth, lineHeight), self.getDest(x, trains), fill="yellow", font=font) #fill destination

			#Only get the slow train data if we are using metrohero data
			if self.wmataActive:
				localminwidth = self.displayWidth - font.getsize(self.getMin(x, trains))[0] - 1 #we want minutes to be right aligned
				draw.text((localminwidth, lineHeight), self.getMin(x, trains), fill="yellow", font=font) #fill mins

			else:
				localminwidth = self.displayWidth - font.getsize(self.getMinWithSlow(x, trains))[0] - 1 #we want minutes to be right aligned
				draw.text((localminwidth, lineHeight), self.getMinWithSlow(x, trains), fill="yellow", font=font) #fill mins

			# print (getLine(x) + "\t" + getCars(x) + "\t" + getDest(x) + "\t" + getMinWithSlow(x)) #UNCOMMENT FOR DEBUG

		return (image, draw)
