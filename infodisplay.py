#!/usr/bin/python
''' Richer Oled information.'''
import serial, subprocess, time, logging, datetime
from oled import Oled
from weather import Weather
import config

class InfoDisplay(Oled):
	'''	Richer info on the oled. '''
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		Oled.__init__(self, 2)
		self.myWeather = Weather()
		self.update_row2(1)
		
	def update_row2(self, temperature_refresh_needed, time_remaining=0):
		'''Time and temperature display.'''
		clock = time.strftime("%R")
		self.logger.info('Update row2:'+clock)
		if temperature_refresh_needed:
			self.temperature = self.myWeather.wunder(config.key, config.locn)
		if True:
			self.writerow(2,
				'{0:5s}  {1:7.1f}^C'.format(clock, float(self.temperature)))
		else:			# a version for debugging
			self.writerow(2,
				'{0:5s}{1:4d}{2:5.1f}^C'.format(clock, time_remaining, float(self.temperature)))		
		return(0)
		