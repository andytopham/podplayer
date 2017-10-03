#!/usr/bin/python
''' Fetch weather information from wunder.'''
import requests
from bs4 import BeautifulSoup
import urllib2
import json
import logging
import datetime
import threading, time
# import keys

class Weather(threading.Thread):
	def __init__(self, key, locn):
		self.Event = threading.Event()
		threading.Thread.__init__(self, name='myweather')
		self.logger = logging.getLogger(__name__)
		self.key = key
		if self.key == 'none':
			print 'No weather key, emulating.'
		self.locn = locn
		self.wunder_temperature = 0

	def run(self):
		print 'Starting weather thread'
		myevent = False
		while not myevent:
			if self.key == 'none':
				self.wunder_temperature = 10
			else:
				self.wunder_temperature = self.wunder(self.key, self.locn)
			print 'Read temp:',self.wunder_temperature
			time.sleep(6)			# temporary - the max allowed per min by wunder
			myevent = self.Event.wait(15*60)		# wait for this timeout or the flag being set.
		print 'Weather exiting.'

	def gettemperature(self,bbckey):
		print 'Fetching BBC temperature'
		self.logger.debug("Fetching bbc temperature")
		try:
			string = 'http://open.live.bbc.co.uk/weather/feeds/en/'+bbckey+'/observations.rss'
			soup = BeautifulSoup(requests.get(string).text,"html.parser")
		except HTTPError, e:
			self.logger.error('Failed to fetch temperature')
			temperature = 0
		except URLError, e:
			self.logger.error('Failed to reach temperature website')
			temperature = 1
		except:
			self.logger.error('Unknown error fetching temperature')
			temperature = 99
		try:
			g = unicode(soup.item.description)
			found = re.search(": [0-9]*.*C",g)
			ggg = re.search("[0-9][0-9]|[0-9]",found.group())
			temperature=ggg.group()
			#this example shows how to get the temperatures from the forecast...
			#temperatures=[str(tem.contents[0]) for tem in table.find_all("span",class_="units-value temperature-value temperature-value-unit-c")]
		except:
			self.logger.error('Failed to convert temperature.')
			temperature=0
		self.logger.info('Temperature='+str(temperature))
		return(temperature)

	def wunder(self,key,locn):
		print 'Fetching wunder temperature'
		self.logger.debug("Fetching wunder temperature")
		f = urllib2.urlopen('http://api.wunderground.com/api/'+key+'/conditions/q/'+locn+'.json')
		json_string = f.read()
		parsed_json = json.loads(json_string)
		#location = parsed_json['location']['city']
		temp_c = parsed_json['current_observation']['temp_c']
		self.logger.info("Current temperature is: %s" % (temp_c))
		f.close()
		return(str(temp_c))

if __name__ == "__main__":
	logging.basicConfig(filename='log/weather.log', filemode='w', level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+
					". Running weather class as a standalone app")

	print "Fetching weather info"
	myWeather = Weather(keys.key, keys.locn)
	myWeather.start()
	print 'Wunder thread now running'
	print 'Current threads'
	print threading.enumerate()
	time.sleep(5)
	if myWeather.is_alive:
		print 'Weather still alive'
	myWeather.Event.set()			# send the stop signal
	time.sleep(3)
	if myWeather.is_alive:
		print 'Weather still alive'
	print threading.enumerate()
	print 'Ending main.'
#	myWeather.wunder()
