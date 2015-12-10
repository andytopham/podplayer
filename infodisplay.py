#!/usr/bin/python
''' Richer Oled information.'''
import subprocess, time, logging, datetime
from weather import Weather
import config
if config.board == 'oled':
	from uoled import Oled
else:
	from tft import Screen as Oled 

TITLE_ROW = 0	# for tft
# TITLE_ROW = 0	# for uoled and oled

class InfoDisplay(Oled):
	'''	Richer info on the oled. '''
	def __init__(self,rowcount=2):
		self.logger = logging.getLogger(__name__)
		self.rowcount = rowcount
		Oled.__init__(self, rowcount)		# We are a subclass, so need to be explicit about which init
		self.rowcount, self.rowlength = self.info()
		self.writerow(TITLE_ROW, 'Starting up...'.center(self.rowlength))
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
		self.write_radio_extras(clock, self.temperature)
		self.writelabels()
		return(0)
	
	def proginfo(self,string):
		'''Display up to 3 rows of the program name and details.'''
		self.logger.info('proginfo:'+string)
		retstr = self._find_station_name(string)
		if retstr:						# if the station is recognised.
			self.writerow(TITLE_ROW,retstr.center(self.rowlength))
			string = string[len(retstr)+4:]		# trim off the station name.
		else:
			self.writerow(TITLE_ROW,string[:self.rowlength].ljust(self.rowlength))
			string = string[self.rowlength:]	
		for i in range(TITLE_ROW+1, self.rowcount):
			string = self._process_next_row(i,string)
		return(0)
		
	def _process_next_row(self, row, string):
		if len(string) > 0:
			if string[0] == ' ':				# strip off any leading space.
				string = string[1:]
			self.writerow(row,string[:self.rowlength].ljust(self.rowlength))
			string = string[self.rowlength:]
		return(string)
	
	def _find_station_name(self,string):
		''' Just recognise the BBC station.'''
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
		