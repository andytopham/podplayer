#!/usr/bin/python
''' Richer Oled information.'''
import subprocess, time, logging, datetime
from weather import Weather
import config
if config.board == 'oled':
	from uoled import Oled
else:
	from tft import Screen as Oled 

class InfoDisplay(Oled):
	'''	Richer info on the oled. '''
	def __init__(self,rowcount=2):
		self.logger = logging.getLogger(__name__)
		self.rowcount = rowcount
		Oled.__init__(self, rowcount)		# We are a subclass, so need to be explicit about which init
		print 'row length ',self.rowlength
		self.writerow(1, 'Starting up...'.center(self.rowlength))
		self.myWeather = Weather()
		self.update_row2(1)
		self.lasttime = 0
		self.delta = 0.001
	
	def update_row2(self, temperature_refresh_needed=False, time_remaining=0):
		'''Time and temperature display on the info line = bottom row'''
		try:
			clock = time.strftime("%R")
			self.logger.info('Update row2:'+clock)
			if temperature_refresh_needed:
				self.temperature = self.myWeather.wunder(config.key, config.locn)
		except:
			self.logger.warning('Error in updaterow2, part 1.')
			return(1)
		self.writerow(self.rowcount,
			'{0:5s}{1:7.1f}^C'.format(clock.ljust(self.rowlength-9), float(self.temperature)))		
		return(0)
	
	def proginfo(self,string):
		self.logger.info('proginfo:'+string)
		retstr = self.find_station_name(string)
		if retstr:
			offset = len(retstr)		# not enough - bodge below
			offset += 4
			self.writerow(1,retstr.center(self.rowlength))
			self.writerow(2,string[offset:self.rowlength+offset])
			self.writerow(3,string[self.rowlength+offset:(self.rowlength*2)+offset].ljust(self.rowlength))
		else:
			self.writerow(1,string[0:self.rowlength])
			self.writerow(2,string[self.rowlength+offset:(self.rowlength*2)+offset])
			# strip off any leading space.
			if string[(self.rowlength*2)+offset] == ' ':
				self.writerow(3,string[(self.rowlength*2)+1+offset:(self.rowlength*3)+1+offset].ljust(self.rowlength))		
			else:
				self.writerow(3,string[(self.rowlength*2)+offset:(self.rowlength*3)+offset].ljust(self.rowlength))		

	def find_station_name(self,string):
		a = string.split()
		if a[0] == 'BBC':
			retstr = a[0]+' '+a[2]+a[3]
			return(retstr)
		else:
			return(False)
	
	def displayvol(self, string):
		if self.rowlength == 16:
			self.writerow(1, string)	
		else:
			self.writerow(4, string)	

	def update_row3(self, elapsed=0, maxelapsed=0):
		'''Show time gone.'''
		if ((elapsed - self.lasttime) > self.delta) or ((self.lasttime - elapsed) > self.delta): 
			self.writerow(3,'Now={0:4.2f}s Max={1:5.2f}s'.format(elapsed, maxelapsed))
			self.lasttime = elapsed
		return(0)

	def update_row4(self,prog='Test'):
		'''Show test code.'''
		self.writerow(4,prog)
		return(0)
		
	def update_whole_display(self):
		self.update_row2()
		self.update_row3()
		self.update_row4()
		return(0)
		
	def scroll(self, string):
		return(0)
		