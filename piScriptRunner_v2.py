#!/usr/bin/python3

#Always set loggers first, even before other input, otherwise issues happen
import logging, time, incidents
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import os

logging.basicConfig(
	handlers=[RotatingFileHandler('wmata.log', maxBytes=10*1024*1024, backupCount=5)],
	level=logging.DEBUG,
	format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
	datefmt='%m/%d/%Y %I:%M:%S %p')

#Rest of program begins here
import threading, time, wmata_v8, sys, traceback, os
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import ImageFont

load_dotenv()

myLines = ["OR","SV"] # Need to figure out how to set this as an env variable...

wmataApiKey = os.getenv('WMATA_API_KEY')
weatherApiKey = os.getenv('WEATHER_API_KEY')
latitude = os.getenv('LATITUDE')
longitude = os.getenv('LONGITUDE')
stationCode = os.getenv('STATION_CODE')
displayStart = os.getenv('DISPLAY_START')
displayStartWeekend = os.getenv('DISPLAY_START_WEEKEND')
displayStop = os.getenv('DISPLAY_STOP')
fontPath = os.getenv('FONT_PATH')
fontPathIncident = os.getenv('FONT_PATH_INCIDENT')


print(time.strftime("%X"))

#NOTE: the wmata python file specifies a number of options that can be personalized, this is where you would pass the specified option flags
board = wmata_v8.WmataBoard(wmataApiKey, weatherApiKey, latitude, longitude, stationCode=stationCode, myLines=myLines)

options = RGBMatrixOptions()
options.rows = board.displayHeight
options.cols = board.displayWidth
options.hardware_mapping = 'adafruit-hat-pwm' # hardcoded to adafruit-hat since that's what I have!
options.gpio_slowdown = 2 #Set to two for RaspPi 3 B+ model with display, which was being funky
options.brightness = 30

matrix = RGBMatrix(options=options) #Initialize the matrix

bufferimage = matrix.CreateFrameCanvas()

font = ImageFont.load(fontPath)

leftPos = board.displayWidth

displayRefreshRate = 3


def dataRefresher():
	board.refreshData()

# Takes in seconds to loop
def looper():
	#leftPos stores the current X coordianate of where to draw
	global leftPos, displayRefreshRate

	while True:
		displayHours()

		numAlerts = len(board.alertData)
		output = board.dataDrawer(fontPath)
		image = output[0]
		draw = output[1]

		if board.displayHeader and not board.displayWeather:
			if numAlerts == 0:
				print("drawing time")
				board.displayDate = True
				board.drawTime(draw,font)
			else:
				drawAlerts(draw)
		elif board.displayWeather:
			drawAlerts(draw)
		else: 
			board.displayDate = True
			board.drawTime(draw,font)

		bufferimage.SetImage(image)
		matrix.SwapOnVSync(bufferimage)
		time.sleep(displayRefreshRate)

def drawAlerts(drawObj):

	global leftPos, displayRefreshRate

	draw = drawObj

	displayRefreshRate = 0.04 #if we're scrolling text, display needs to update fast

	board.displayDate = False #Don't display the date bar (we will include in string)

	alertString = "" #Initialize alert string to 0

	currentEndOfString = 0 #initialize this length variable to 0

	alertHeight = board.displayHeight - 10 # Bottom of my board

	#Intentionally, this code displays the date and "ALERT" text in between each alert
	#For each alert:

	if board.displayBasicAlerts: 

		for i in board.alertData:

			#Only draw and display the date/time if you are showing header
			#Otherwise, date/time seperately permanently displayed
			if board.displayHeader:
				timeString = time.strftime("%a, %b %d %I:%M %p", time.localtime())

				#Add date + time to the eventual alert string
				alertString += timeString

				#Draw the date + time
				draw.text((leftPos + currentEndOfString,22), timeString, fill="white", font=font)

				#update the width of string counter var
				currentEndOfString = font.getsize(alertString)[0]

			if board.displayWeather:
				alertString += board.weatherString()
				draw.text((leftPos + currentEndOfString, alertHeight), board.weatherString() + " ", fill="white", font=font)
				currentEndOfString = font.getsize(alertString)[0]

			#DRAW THE ALERT:
			alertString += " ALERT: "
			draw.text((leftPos + currentEndOfString, alertHeight), " ALERT: ", fill="red", font=font)
			currentEndOfString = font.getsize(alertString)[0]
			draw.text((leftPos + currentEndOfString, alertHeight), i, fill="white", font=font)
			alertString += " " + i
			currentEndOfString = font.getsize(alertString)[0]

				#This only applies if the above for-loop did not run

		if len(board.alertData) == 0:
			alertString += board.weatherString()
			draw.text((leftPos + currentEndOfString, alertHeight), board.weatherString(), fill="white", font=font)
			currentEndOfString = font.getsize(alertString)[0]

	else: 

		# these are the fancier alerts
		# i found the code for the 
			if board.displayHeader: 
				timeString = time.strftime("%a, %b %d %I:%M %p", time.localtime())

				#Add date + time to the eventual alert string
				alertString += timeString

				#Draw the date + time
				draw.text((leftPos + currentEndOfString,22), timeString, fill="white", font=font)

				#update the width of string counter var
				currentEndOfString = font.getsize(alertString)[0]

				if board.displayWeather:
					alertString += board.weatherString()
					draw.text((leftPos + currentEndOfString, alertHeight), alertString + " ", fill="white", font=font)
					currentEndOfString = font.getsize(alertString)[0]

			else: 
				timeString = time.strftime("%a, %b %d %I:%M %p", time.localtime())

				#Add date + time to the eventual alert string
				alertString += timeString + " "

				#update the width of string counter var
				currentEndOfString = font.getsize(alertString)[0]
					
				if board.displayWeather:
					alertString += board.weatherString()
					draw.text((leftPos + currentEndOfString, alertHeight), alertString + " ", fill="white", font=font)
					currentEndOfString = font.getsize(alertString)[0]


	alertStringWidth = currentEndOfString

	leftPos = leftPos - 1

	#Not sure but I think this prevents an absurdly long loop of white space between alerts
	
	if leftPos < ((alertStringWidth + board.displayWidth)*-1):

		leftPos = board.displayWidth

		if board.fancyAlerts:

			if len(board.alertData) > 0 and (time.time() - board.lastFancyAlertDisplayTime >= 7): 

				matrix.Clear()

				for alert in board.alertData: 

					incidents.draw_incident(matrix, fontPathIncident, alert)

				board.lastFancyAlertDisplayTime = time.time()


def displayHours():
	if time.localtime().tm_wday > 5:
		if displayStartWeekend <= time.localtime().tm_hour:
			return
	elif displayStart <= time.localtime().tm_hour:
		return
	matrix.Clear()
	time.sleep(300)
	displayHours()

class DataThreader():

	def __init__(self):
		thread = threading.Thread(target=self.run)
		thread.daemon = True                            # Daemonize thread
		thread.start()                                  # Start the execution
	def run(self):
		""" Method that runs forever """
		while True:
			dataRefresher()
			time.sleep(2) #Hard coded fail safe to never check data more than once every 2 seconds

data = DataThreader()

try:
	logging.info("*************************************************")
	logging.info('Started program')
	looper()
except KeyboardInterrupt as err:
	logging.info("KeyboardInterrupt")
	matrix.Clear()
	exit()
except IndexError as err:
	logging.error("Index Error but continuing: ", exc_info=True)
	logging.error("Number of trains at index error: " + str(board.numTrains))
	logging.error("Train data at index error: " + str(board.upcomingtrains))
	time.sleep(3)
	pass
except:
	logging.critical("Program closing", exc_info=True)
	logging.critical("Weather Data:" + str(board.weatherData))
	matrix.Clear()
	exit()
