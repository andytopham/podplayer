#!/usr/bin/python
''' Richer Oled information.'''
import subprocess, time, logging, datetime
from weather import Weather
import config

### Display layout
# ROWS 0 to 3 = Prog info
TITLE_ROW = 0	# for tft
TIMING_ROW = 7
NEXT_STATION_ROW = 8
#
# radio extras
# button labels
###

class InfoDisplay():
	'''	Richer info on the oled. '''
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		if config.board == 'oled':
			import oled
			self.myScreen = oled.Oled()
		else:
			import tft
			self.myScreen = tft.Screen()
		self.rowcount, self.rowlength = self.myScreen.info()
		self.myScreen.writerow(TITLE_ROW, 'Starting up...'.center(self.rowlength))
		self.myWeather = Weather()
		self.update_info_row(True)
		self.lasttime = 0
		self.delta = 0.001

	def writerow(self, row, string):
		self.myScreen.writerow(row, string)
		
	def update_info_row(self, temperature_refresh_needed=False):
		'''Time and temperature display on the info line = bottom row'''
		try:
			clock = time.strftime("%R")
			self.logger.info('Update info row:'+clock)
			if temperature_refresh_needed:
				self.temperature = self.myWeather.wunder(config.key, config.locn)
		except:
			self.logger.warning('Error in update info row, part 1.')
			return(1)
		self.myScreen.write_radio_extras(clock, self.temperature)
		self.myScreen.write_button_labels()
		return(0)
	
	def show_prog_info(self,string):
		'''Display up to 2 rows from bottom of display of the program name and details.'''
		self.logger.info('proginfo:'+string)
		retstr = self._find_station_name(string)
		if retstr:						# if the station is recognised.
			self.myScreen.writerow(TITLE_ROW,retstr.center(self.rowlength))
			string = string[len(retstr)+4:]		# trim off the station name.
		else:
			self.myScreen.writerow(TITLE_ROW,string[:self.rowlength].ljust(self.rowlength))
			string = string[self.rowlength:]	
		for i in range(TITLE_ROW+1, self.rowcount-2):
			string = self._process_next_row(i,string)
		return(0)
		
	def _process_next_row(self, row, string):
		if len(string) > 0:
			if string[0] == ' ':				# strip off any leading space.
				string = string[1:]
			self.myScreen.writerow(row,string[:self.rowlength].ljust(self.rowlength))
			string = string[self.rowlength:]
		else:
			if row < 4:
				string = ''
				self.myScreen.writerow(row,string)
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
		self.myScreen.writerow(self.rowcount-1, string)	

	def show_timings(self, elapsed=0, maxelapsed=0):
		'''Show time gone.'''
		if ((elapsed - self.lasttime) > self.delta) or ((self.lasttime - elapsed) > self.delta): 
			self.myScreen.writerow(TIMING_ROW,'Now={0:4.2f}s Max={1:5.2f}s'.format(elapsed, maxelapsed))
			self.lasttime = elapsed
		return(0)

	def show_next_station(self,prog='Test'):
		'''Show test code.'''
		self.myScreen.writerow(NEXT_STATION_ROW, prog[:self.rowlength])
		return(0)
		
	def _update_whole_display(self):
		self.update_row2()
		self.update_row3()
		self.update_row4()
		return(0)
	
	def scroll(self,row,string):
		for i in range(len(string)+1):
			self.myScreen.writerow(row,string[i:i+self.rowlength])
		return(0)

	def writelabels(self, next = False, stop = False):
		self.myScreen.write_button_labels(next, stop)
		return(0)
		
if __name__ == "__main__":
	print 'Infodisplay test'		
	myID = InfoDisplay()
	print dir(myID)
	myID.show_prog_info('This is a very long text string to test where the programme information would normally be printed.')
	myID.scroll(6,'This is a very long text string to test where the programme information would normally be printed.')
	