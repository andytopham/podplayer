#!/usr/bin/python
''' Richer Oled information.'''
import subprocess, time, logging, datetime, sys, threading
from weather import Weather
import keys

# ToDo: Add scrolling, based on overflow from row0.
#   Put this into a Timer.


### Display layout for tft
# ROWS 0 to 3 = Prog info
TITLE_ROW = 0	# for tft
TIMING_ROW = 7
NEXT_STATION_ROW = 8
#
# radio extras
# button labels
###
SCROLL_PAUSE = -5
INFOROWUPDATEPERIOD = 60

class InfoDisplay():
	'''	Richer info on the oled. '''
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.logger.info("Starting InfoDisplay class")
		print 'board = ',keys.board
		if keys.board == 'oled4':
			import oled
			self.myScreen = oled.Screen(4)
		elif keys.board == 'oled2':
			import oled
			self.myScreen = oled.Screen(2)
		elif keys.board == 'uoled':
			import uoled
			self.myScreen = uoled.Screen()
			self.myScreen.start()
		elif keys.board == 'tft':
			import tft
			self.myScreen = tft.Screen()
		else:
			print 'No display specified in keys file. Exiting.'
			self.logger.error('No display specified in keys file. Exiting.')
			sys.exit()
		self.rowcount, self.rowlength = self.myScreen.info()
		self.writerow(TITLE_ROW, 'Starting up...'.center(self.rowlength))
		self.myWeather = Weather(keys.key, keys.locn)
		self.myWeather.start()
		self.update_info_row()
		self.lasttime = 0
		self.delta = 0.001
		self.scroll_pointer = SCROLL_PAUSE

	def cleanup(self):
		self.myWeather.Event.set()			# send the stop signal
		self.myScreen.Event.set()
		
	def clear(self):
		self.myScreen.clear()
	
	def writerow(self, row, string):
		if row < self.rowcount:
			self.myScreen.q.put([row, string])	# add to the queue

	def _end_display(self):
		self.myScreen.Event.set()			# send the stop signal
	
	def update_info_row(self):
		'''Time and temperature display on the info line = bottom row.
			This now repeats itself courtesy of the Timer.'''
		clock = time.strftime("%R")
		self.logger.info('Update info row:'+clock)
		self.myScreen.write_radio_extras(clock, self.myWeather.wunder_temperature)
		self.myScreen.write_button_labels(False, False)
		self.t = threading.Timer(INFOROWUPDATEPERIOD, self.update_info_row)	# run every 60secs
		self.t.start()
		self.t.name = 'inforow'
		return(0)
	
	def show_prog_info(self,string):
		'''Display up to 2 rows from bottom of display of the program name and details.'''
		self.logger.info('proginfo:'+string)
		retstr, string = self._find_station_name(string)
		if retstr:						# if the station is recognised.
			self.myScreen.q.put([TITLE_ROW,retstr.center(self.rowlength)])
		else:
			self.myScreen.q.put([TITLE_ROW,string[:self.rowlength].ljust(self.rowlength)])
			string = string[self.rowlength:]	
		for i in range(TITLE_ROW+1, self.myScreen.last_prog_row+1):
			string = self._process_next_row(i,string)
		return(0)
## Need to scroll the last row ###		
	def _process_next_row(self, row, string):
		if len(string) > 0:
			if string[0] == ' ':				# strip off any leading space.
				string = string[1:]
			self.myScreen.q.put([row,string[:self.rowlength].ljust(self.rowlength)])
			string = string[self.rowlength:]
		else:
			if row < 4:
				string = ''
				self.myScreen.q.put([row,string])
		return(string)
	
	def _find_station_name(self,string):
		''' Just recognise the BBC station.'''
		a = string.split()
		if a[0] == 'BBC':
			if a[3] == '6':
				retstr = a[0]+' '+a[2]+a[3]+' '+a[4]
				remainder = string[len(retstr)+4:]		# trim off the station name.
			elif a[4] == 'Extra':					# BBC Radio 4 Extra
				retstr = a[0]+' '+a[2]+a[3]+' '+a[4]
				remainder = string[len(retstr)+4:]		# trim off the station name.
			else:
				retstr = a[0]+' '+a[2]+a[3]
				remainder = string[len(retstr)+4:]		# trim off the station name.
			return(retstr, remainder)
		else:
			return(False, string)
	
#	def displayvol(self, string):
#		self.myScreen.writerow(self.rowcount-1, string)	

	def show_timings(self, elapsed=0, maxelapsed=0):
		'''Show time gone.'''
		if ((elapsed - self.lasttime) > self.delta) or ((self.lasttime - elapsed) > self.delta): 
			self.myScreen.writerow(TIMING_ROW,'Now={0:4.2f}s Max={1:5.2f}s'.format(elapsed, maxelapsed))
			self.lasttime = elapsed
		return(0)

#	def show_next_station(self,prog='Test'):
#		'''Show test code.'''
#		self.myScreen.writerow(NEXT_STATION_ROW, prog[:self.rowlength])
#		return(0)
		
	def _update_whole_display(self):
		self.update_row2()
		self.update_row3()
		self.update_row4()
		return(0)

# This needs putting into a timer.....####		
	def scroll(self,row,string):
		if self.rowcount > 2:	# do not scroll large display
			return(0)
		if self.scroll_pointer < 0:
			self.myScreen.writerow(row,string[0:self.rowlength])
		else:
			self.myScreen.writerow(row,string[self.scroll_pointer:self.scroll_pointer+self.rowlength])
		self.scroll_pointer += 1
		if  self.scroll_pointer > len(string):
			self.scroll_pointer = SCROLL_PAUSE
		return(0)

	def writelabels(self, next = False, stop = False):
		self.logger.info('writelabels')
		self.myScreen.write_button_labels(next, stop)
		return(0)
		
if __name__ == "__main__":
	logging.basicConfig(filename='log/infodisplay.log',
						filemode='w',
						level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running infodisplay class as a standalone app")

	print 'Infodisplay test'		
	myID = InfoDisplay()
	myID.show_prog_info('This is a very long text string to test where the programme information would normally be printed.')
#	print 'Weather thread has been forked.'
	time.sleep(8)
	myID.cleanup()
#	print 'Weather has been told to stop.'
	print 'Main prog is finished.'
	