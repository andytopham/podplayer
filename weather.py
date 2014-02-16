#!/usr/bin/python
''' 
  Module to fetch weather information from the web.
  Imported by iradio.
  Methods:
 	
'''
import requests
from bs4 import BeautifulSoup
import urllib2
import json
import logging
import datetime

class weather:
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		temperature = 0

	def gettemperature(self,bbckey):
		self.logger.debug("Fetching temperature")
		try:
			string = 'http://open.live.bbc.co.uk/weather/feeds/en/'+bbckey+'/observations.rss'
			soup = BeautifulSoup(requests.get(string).text)
		except HTTPError, e:
			self.logger.error("Failed to fetch temperature")
			temperature = 0
		except URLError, e:
			self.logger.error("Failed to reach temperature website")
			temperature = 1
		else:
			g = unicode(soup.item.description)
			found = re.search(": [0-9]*.*C",g)
			ggg = re.search("[0-9][0-9]|[0-9]",found.group())
			temperature=ggg.group()
			#this example shows how to get the temperatures from the forecast...
			#temperatures=[str(tem.contents[0]) for tem in table.find_all("span",class_="units-value temperature-value temperature-value-unit-c")]
			return(temperature)

	def wunder(self,key,locn):
		self.logger.debug("Fetching wunder temperature")
		f = urllib2.urlopen('http://api.wunderground.com/api/'+key+'/conditions/q/'+locn)
		json_string = f.read()
		parsed_json = json.loads(json_string)
		#location = parsed_json['location']['city']
		temp_c = parsed_json['current_observation']['temp_c']
		self.logger.info("Current temperature is: %s" % (temp_c))
		f.close()
		return(str(temp_c))
		
if __name__ == "__main__":
	logging.basicConfig(filename='log/weather.log',
						filemode='w',
						level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+
					". Running weather class as a standalone app")

	print "Fetching weather info"
	myWeather = weather()
	myWeather.wunder()
	