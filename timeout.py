#!/usr/bin/python
'''Control a series of timeouts.'''

import time
import datetime
import logging
import config

# all in minutes
OLEDTIMEOUT = 1
TEMPERATURETIMEOUT = 15
STATIONTIMEOUT = 120
AUDIOTIMEOUT = 30

class Timeout:
	def __init__(self, verbose=0):
		self.logger = logging.getLogger(__name__)
		self.logger.info('Setting timeouts: verbose='+str(verbose))
		if verbose == 1:
			self.logger.info('Timeouts(mins): OLED='+str(OLEDTIMEOUT)
				+' Temperature='+str(TEMPERATURETIMEOUT)
				+' Station='+str(STATIONTIMEOUT)
				+' AudioTimeout='+str(AUDIOTIMEOUT))
			self.oledupdatefreq = datetime.timedelta(minutes=OLEDTIMEOUT)
			self.temperatureupdatefreq = datetime.timedelta(minutes=TEMPERATURETIMEOUT)
			self.stationupdatefreq = datetime.timedelta(minutes=STATIONTIMEOUT)	# a wild guess at how often the bbc change the key
			self.audiotimeoutfreq = datetime.timedelta(minutes=AUDIOTIMEOUT)
		else:
			self.logger.info('Timeouts(mins): OLED='+str(OLEDTIMEOUT)
				+' Temperature='+str(TEMPERATURETIMEOUT)
				+' Station='+str(STATIONTIMEOUT)
				+' AudioTimeout='+str(AUDIOTIMEOUT))
			self.oledupdatefreq = datetime.timedelta(minutes=OLEDTIMEOUT)
			self.temperatureupdatefreq = datetime.timedelta(minutes=TEMPERATURETIMEOUT)
			self.stationupdatefreq = datetime.timedelta(minutes=STATIONTIMEOUT)	# a wild guess at how often the bbc change the key
			self.audiotimeoutfreq = datetime.timedelta(minutes=AUDIOTIMEOUT)
		#initialise timers
		self.start = datetime.datetime.now()
		self.oledlastupdate = datetime.datetime.now()
		self.temperaturestart = datetime.datetime.now()
		self.stationstart = datetime.datetime.now()
		self.audiostart = datetime.datetime.now()

	def checktimeouts(self):
		now = datetime.datetime.now()
		if (now - self.start) > self.oledupdatefreq:
			self.logger.info('Timeout: oled')
			self.start = datetime.datetime.now()
			return(config.UPDATEOLED)
		if (now - self.temperaturestart) > self.temperatureupdatefreq:
			self.logger.info('Timeout: temperature')
			self.temperaturestart = datetime.datetime.now()
			return(config.UPDATETEMPERATURE)
		if (now - self.stationstart) > self.stationupdatefreq:
			self.logger.info('Timeout: station')
			self.stationstart = datetime.datetime.now()
			return(config.UPDATESTATION)
		if (now - self.audiostart) > self.audiotimeoutfreq:
			self.logger.warning("*Audio timeout*")
			self.audiostart = datetime.datetime.now()
			return(config.AUDIOTIMEOUT)
		return(0)
		
	def resetAudioTimeout(self):
		self.audiostart = datetime.datetime.now()
	