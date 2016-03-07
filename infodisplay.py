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

class InfoDisplay(threading.Thread):
	'''	Richer info on the oled. '''
	def __init__(self, testmode = False):
		self.logger = logging.getLogger(__name__)
		threading.Thread.__init__(self, name='infodisplay')
		self.logger.info("Starting InfoDisplay class")
		self.myWeather = Weather(keys.key, keys.locn)
		self.myWeather.start()
		self.chgvol_flag = False
		self.vol_string = ' '
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
#			self.myScreen.start()
		elif keys.board == 'tft':
			import tft
			self.myScreen = tft.Screen()
		else:
			print 'No display specified in keys file. Exiting.'
			self.logger.error('No display specified in keys file. Exiting.')
			sys.exit()
		self.ending = False
		self.myScreen.start()
		self.rowcount, self.rowlength = self.myScreen.info()
		self.writerow(TITLE_ROW, 'Starting up...'.center(self.rowlength))
		self.update_info_row()
		self.lasttime = 0
		self.delta = 0.001
		self.scroll_pointer = SCROLL_PAUSE
		self.scroll_string = '       '
		self.prog = 'Info test'
		if testmode:
			self.timer = 2
		else:
			self.timer = INFOROWUPDATEPERIOD
#		self.scroll()
		
	def cleanup(self):
		self.ending = True					# must be first line. 
		self.t.cancel()						# cancel timer for update display
#		self.scrollt.cancel()
		self.myWeather.Event.set()			# send the stop signal
		self.myScreen.Event.set()
		time.sleep(2)
		self.logger.info('Ended infodisplay.')
		
	def clear(self):
		'''Clear screen.'''
		self.myScreen.clear()
	
	def writerow(self, row, string):
		if row < self.rowcount:
			self.myScreen.q.put([row, string])	# add to the queue

	def update_display(self):
		'''Update the whole display, including the prog info and the status line.'''
		self.logger.info('Updating display')
		self.update_info_row()
		self.show_prog_info(self.prog)
		if not self.ending:
			self.t = threading.Timer(self.timer, self.update_display)	
			self.t.start()
			self.t.name = 'displayupdate'
		return(0)
		
	def update_info_row(self):
		'''Time and temperature display on the info line = bottom row.
			This now repeats itself courtesy of the Timer.'''
		clock = time.strftime("%R")
		self.logger.info('Update info row:'+clock)
		if self.chgvol_flag:
			self.myScreen.write_radio_extras(self.vol_string, '  ', True)
		else:
			self.myScreen.write_radio_extras(clock, self.myWeather.wunder_temperature)
		self.myScreen.write_button_labels(False, False)
		return(0)
	
	def show_prog_info(self,string):
		'''Display up to 2 rows from bottom of display of the program name and details.'''
		self.logger.info('show_prog_info:'+string)
		retstr, string = self._find_station_name(string)
		if retstr:						# if the station is recognised.
			self.myScreen.q.put([TITLE_ROW,retstr.center(self.rowlength)])
		else:
			self.myScreen.q.put([TITLE_ROW,string[:self.rowlength].ljust(self.rowlength)])
			string = string[self.rowlength:]	
		for i in range(TITLE_ROW+1, self.myScreen.last_prog_row+1): # run through the rest of the rows.
			string = self._process_next_row(i,string)
		return(0)
		
	def _process_next_row(self, row, string):
		'''Called by show_prog_info to process all rows after first row.'''
		if len(string) > 0:
			if string[0] == ' ':				# strip off any leading space.
				string = string[1:]
			if row == self.myScreen.last_prog_row:
				self.myScreen.q.put([row,string[:self.rowlength].ljust(self.rowlength)])
#				self.scroll_string = string+' '	# tag a space on end to help delete trailing scrolling chars
			else:
				self.myScreen.q.put([row,string[:self.rowlength].ljust(self.rowlength)])
				string = string[self.rowlength:]
		else:									# nothing left to show
			if row < 4:
				string = '                         '	# blank the last rows
				self.myScreen.q.put([row,string])
				self.scroll_string = '           '
		return(string)
	
	def _find_station_name(self,string):
		'''Called by show_prog_info. Decode the BBC station from the proginfo.'''
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
	
	def show_timings(self, elapsed=0, maxelapsed=0):
		'''Show time gone.'''
		if ((elapsed - self.lasttime) > self.delta) or ((self.lasttime - elapsed) > self.delta): 
			self.myScreen.writerow(TIMING_ROW,'Now={0:4.2f}s Max={1:5.2f}s'.format(elapsed, maxelapsed))
			self.lasttime = elapsed
		return(0)
		
	def scroll(self):
		if len(self.scroll_string) > 10:
			row = 2
			if self.scroll_pointer < 0:
				self.myScreen.q.put([row, self.scroll_string[0:self.rowlength]])
			else:
				self.myScreen.q.put([row, self.scroll_string[self.scroll_pointer:self.scroll_pointer+self.rowlength]])
			self.scroll_pointer += 1
			if  self.scroll_pointer > (len(self.scroll_string)-15):
				self.scroll_pointer = SCROLL_PAUSE
		if not self.ending:
			self.scrollt = threading.Timer(.5, self.scroll)
			self.scrollt.start()
			self.scrollt.name = 'scroll'
		return(0)

	def writelabels(self, next = False, stop = False):
		'''Show the action labels on the screen.'''
		self.logger.info('writelabels')
		self.myScreen.write_button_labels(next, stop)
		return(0)
		
if __name__ == "__main__":
	logging.basicConfig(filename='log/infodisplay.log',
						filemode='w',
						level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running infodisplay class as a standalone app")

	print 'Infodisplay test'		
	myID = InfoDisplay(testmode = True)
	myID.update_display()
#	print threading.enumerate()
#	myID.writelabels(True)
#	time.sleep(2)
	string = ['String zero.',
		'String1. Lets put a lot of text here so that it wraps and in fact need plenty to test scroll.', 
		'Strings 2.', 
		'Third string', 
		'Prog name goes here. And then the extra super good stuff in the info goes into these lines.', 
		'Final string']
	for i in range(3):
		print 'String ',i
		myID.prog = string[i]
		time.sleep(15)
	print 'cleaning up'
	myID.cleanup()
	print threading.enumerate()
	print 'Main prog is finished.'
	