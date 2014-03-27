#!/usr/bin/python
''' Richer Oled information.'''
import serial
import subprocess, time, logging, datetime
import config
from oled import Oled
from weather import Weather

class InfoDisplay(Oled):
	'''	Richer info on the oled. '''
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		Oled.__init__(self, 2)
		self.myWeather = Weather()
		self.update_row2(1)
		
	def update_row2(self, temperature_refresh_needed, time_remaining=0):
		'''Time and temperature display.'''
		self.logger.info('Update row2:'+time.strftime("%R"))
		if temperature_refresh_needed:
			self.temperature = self.myWeather.wunder(config.key, config.locn)
		if time_remaining == 0:
			self.writerow(2,
				time.strftime("%R")
				+"     {0:4.1f}".format(float(self.temperature))
				+"^C ")
		else:
			self.writerow(2,
				time.strftime("%R")
				+'  '
				+str(time_remaining)
				+" {0:4.1f}".format(float(self.temperature))
				+"^C ")		
		return(0)
		