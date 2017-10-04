#!/usr/bin/python
''' Richer Oled information.'''
import subprocess, time, logging, datetime, sys, threading
from weather import Weather
import keys
import importlib

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
CLEANUPTIMEOUT = 5

class InfoDisplay(threading.Thread):
	'''	Richer info on the oled. '''
	def __init__(self, testmode = False, scrolling = False):
		self.logger = logging.getLogger(__name__)
		threading.Thread.__init__(self, name='infodisplay')
		self.Event = threading.Event()
		self.logger.info("Starting InfoDisplay class")
		self.chgvol_flag = False
		self.vol_string = ' '
		if keys.board not in ['oled4', 'oled2', 'lcd', 'uoled', 'tft', 'emulator']:
			print 'Error: display type not recognised.'
			sys.exit()			
		print 'Infodisplay board = ',keys.board
		board = importlib.import_module(keys.board)
		self.myScreen = board.Screen()
		if keys.board == 'oled2':
			self.myScreen.set_rowcount(2)
		self.myWeather = Weather(keys.wunder, keys.locn)
		self.myWeather.start()
		self.ending = False
		self.myScreen.start()
		self.rowcount, self.rowlength = self.myScreen.info()
		self.writerow(TITLE_ROW, 'Starting up...'.center(self.rowlength))
#		self.update_info_row()
		self.lasttime = 0
		self.delta = 0.001
		self.scroll_pointer = SCROLL_PAUSE
		self.scroll_string = '       '
		self.prog = 'Info test'
		if testmode:
			self.timer = 2
		else:
			self.timer = INFOROWUPDATEPERIOD
		self.scrolling = scrolling
		self.told = time.clock()
		
	def cleanup(self):
		self.ending = True	# must be first line.
		time.sleep(1)		# these delays needed to get cleanup to work
		self.Event.set()	# stop the display updates
		try:
			if self.rowcount == 2:
				if self.scrolling:
					self.scrollt.cancel()
					time.sleep(1)
					self.scrollt.cancel()
			else:
				self.t.cancel()						# cancel timer for update display
		except:
			print 'Scroll timer not started'
		self.myWeather.Event.set()			# send the stop signal
		self.myWeather.join(CLEANUPTIMEOUT)				# wait for thread to finish
		if self.myWeather.is_alive():					# so we timed out
			print 'Weather thread did not die'
		self.myScreen.Event.set()
		self.myScreen.join(CLEANUPTIMEOUT)				# wait for thread to finish
		if self.myScreen.is_alive():					# so we timed out
			print 'Screen thread did not die'
		self.logger.info('Finished infodisplay cleanup.')

	def clear(self):
		'''Clear screen.'''
		self.myScreen.clear()

	def writerow(self, row, string):
		if row < self.rowcount:
			self.myScreen.q.put([row, string])	# add to the queue
		else:
			print 'Trying to write to non-existent row:', row
			
	def run(self):
		print 'Starting infodisplay thread'
		myevent = False
		while not myevent:
			self.update_display()
			myevent = self.Event.wait(self.timer)		# wait for this timeout or the flag being set.
		print 'Infodisplay exiting.'

	def update_display(self):
		'''Update the whole display, including the prog info and the status line.'''
		self._update_info_row()
		if self.rowcount == 2:
			if self.scrolling:
				self._scroll(self.prog)
			else:
				self.myScreen.q.put([TITLE_ROW,self.prog[:self.rowlength]])		# just show one row
		else:
			self._show_prog_info(self.prog)
#		if not self.ending:
#			print 'refreshing display update with timer = ',self.timer
#			self.t = threading.Timer(self.timer, self.update_display)
#			self.t.start()
#			self.t.name = 'update_display'
		return(0)

	def _update_info_row(self):
		'''Time and temperature display on the info line = bottom row.
			This now repeats itself courtesy of the Timer.'''
		clock = time.strftime("%H:%M")
		if self.chgvol_flag:
			self.myScreen.write_radio_extras(self.vol_string, '  ', True)
		else:
			self.myScreen.write_radio_extras(clock, self.myWeather.wunder_temperature)
		self.myScreen.write_button_labels(False, False)
		return(0)

	def _show_prog_info(self,string):
		'''Display up to 2 rows from bottom of display of the program name and details.'''
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

	def _scroll(self):
		self.told = time.clock()
#		self._update_info_row()
		if len(self.prog) > 10:
			row = 0	# used to be 2
			if self.scroll_pointer < 0:
				self.myScreen.q.put([row, self.prog[0:self.rowlength]])
			else:
				self.myScreen.q.put([row, self.prog[self.scroll_pointer:self.scroll_pointer+self.rowlength]])
			self.scroll_pointer += 1
			if  self.scroll_pointer > (len(self.prog)-15):
				self.scroll_pointer = SCROLL_PAUSE
		if not self.ending:
			self.scrollt = threading.Timer(.5, self._scroll)
			self.scrollt.start()
			self.scrollt.name = 'scroll'
		self.tstart = time.clock()
		print 'Scroll time:',self.tstart - self.told
		self.told = self.tstart
		return(0)

	def writelabels(self, next = False, stop = False):
		'''Show the action labels on the screen.'''
		self.logger.info('writelabels')
		self.myScreen.write_button_labels(next, stop)
		return(0)

if __name__ == "__main__":
	logging.basicConfig(filename='./log/infodisplay.log',
						filemode='w',
						level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running infodisplay class as a standalone app")

	print 'Infodisplay test'
	myID = InfoDisplay(testmode = True)
#	myID.update_display()
	myID._scroll()
	print 'Timer running'
	string = ['String zero. Here is some text that is long enough to scroll.',
		'String1. Lets put a lot of text here so that it wraps and need plenty to test scroll.',
		'Strings 2.',
		'Final string']
	for i in range(2):
		print 'String ',i
		myID.prog = string[i]
		time.sleep(20)
	print 'cleaning up'
	myID.cleanup()
	print threading.enumerate()
	print 'Main prog is finished.'
