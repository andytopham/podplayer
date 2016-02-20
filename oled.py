#!/usr/bin/python
''' Module to control the picaxe OLED.
  Updated to work with both 16x2 and 20x4 versions.
  Requires new picaxe fw that inverts serial polarity, i.e. N2400 -> T2400.
  The oled modules work fine off the RPi 3v3, which avoids the need for level shifting.
  Requires the installation of the python serial module. Install by:
	sudo apt-get install python-serial
    edit /boot/cmdline.txt to remove all refs to console=ttyAMA0... and kgdboc=ttyAMA0...
    edit /etc/inittab to comment out the last line (T0:23...)
  To get rid of the garbage from the pi bootup...
  edit /boot/cmdline.txt and remove both references to ...ttyAMA0...
  Brightness control: http://www.picaxeforum.co.uk/entry.php?49-Winstar-OLED-Brightness-Control
'''
import serial
import subprocess, time, logging, datetime
import threading, Queue

LOGFILE = 'log/oled.log'
ROWLENGTH4 = 20
ROWLENGTH2 = 16
LAST_PROG_ROW4 = 2
LAST_PROG_ROW2 = 0

class Screen(threading.Thread):
	'''	Oled class. Routines for driving the serial oled. '''
	def __init__(self, rows = 4):
		self.Event = threading.Event()
		self.threadLock = threading.Lock()
		threading.Thread.__init__(self, name='myoled')
		self.q = Queue.Queue(maxsize=6)
		self.rowcount = rows
		if rows == 4:
			self.rowlength = ROWLENGTH4
			self.last_prog_row = LAST_PROG_ROW4
		else:
			self.rowlength = ROWLENGTH2
			self.last_prog_row = LAST_PROG_ROW2
		self.logger = logging.getLogger(__name__)
		self.port = serial.Serial(
			port='/dev/ttyAMA0', 
			baudrate=2400, 
			bytesize=serial.EIGHTBITS,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_TWO)	# Note - not just one stop bit
		#constants
		self.rowselect = [128,192,148,212]	# the addresses of the start of each row
		self.start=0
		self.initialise()

	def run(self):
		while not myevent:
			while not self.q.empty():
				self.writerow(self.q.get())		# items on q must be row,string pairs
				self.q.task_done()
				myevent = self.Event.wait(1)	# wait for this timeout or the flag being set.
		print 'Oled exiting'
	
	def initialise(self):
#		self.port.open()
		self.logger.info("Opened serial port")
		self.port.write(chr(254))		# cmd
		self.port.write(chr(1))			# clear display
		self.start = 0
		self.writerow(0, ' ')
		self.writerow(1, ' ')
		self.writerow(2,'                    ')
		self.writerow(3,'                    ')
		return(0)

	def info(self):
		return(self.rowcount, self.rowlength)

	def write_button_labels(self, next, stop):
		# These are the button labels. No labels with small display.
		if next == True:
			self.logger.info('write_button_labels. Next')
			self.writerow(0,'Next            ')
		if stop == True:
			self.logger.info('write_button_labels. Stop')
			self.writerow(0,'Stop            ')		
		return(0)
	
	def write_radio_extras(self, clock, temperature):
		self.writerow(self.rowcount-1,'{0:5s}{1:7.1f}^C'.format(clock.ljust(self.rowlength-9),float(temperature)))		
		return(0)
	
	def numberofrows(self):
		''' Just returns the number of rows in the display for use by other routines.'''
		return(self.rowcount)
		
	def cleardisplay(self):
		self.port.write(chr(254))		# cmd
		self.port.write(chr(1))			# clear display
		time.sleep(.5)

	def writerow(self,row,string):
		if row < self.rowcount:
			self.port.write(chr(254))		# cmd
			self.port.write(chr(self.rowselect[row]))	# move to start of row
			self.port.write(string[0:self.rowlength].ljust(self.rowlength))
		
	def scroll(self,string):
		if self.rowcount > 2:
			self.writerow(1,string[0:20])
			self.writerow(2,string[20:40].ljust(20))	# pad out the missing chars with spaces
			self.writerow(3,string[40:60].ljust(20))	# pad out the missing chars with spaces
#			pauseCycles=5
#			self.start += 1
#			string = string + ' '			# add a trailing blank to erase as we scroll
#			if self.start > len(string):	# finished scrolling this string, reset.
#				self.start = 0
#			if self.start < pauseCycles:	# only start scrolling after 8 cycles.
#				startpoint=0
#			else:
#				startpoint = self.start-pauseCycles
#			if len(string[40:]) > 21 :		# so it needs scrolling
#			if False:						# temporary to stop the scrolling
#				print "String:",string[40:]
#				print "Startpoint:",startpoint
#				self.writerow(3,string[40+startpoint:60+startpoint])
#			else:
#				self.writerow(3,string[40:60].ljust(20))	# pad out the missing chars with spaces
		else:								# only 2 rows
			pauseCycles=5
			self.start += 1
			string = string + ' '			# add a trailing blank to erase as we scroll
			if self.start > len(string):	# finished scrolling this string, reset.
				self.start = 0
			if self.start < pauseCycles:	# only start scrolling after 8 cycles.
				startpoint=0
			else:
				startpoint = self.start-pauseCycles
			self.writerow(1,string[startpoint:startpoint+self.rowlength])
		return(0)
	
	def screensave(self):
		while True:
			for j in range(self.rowcount):
				self.writerow(j,".")
				for i in range(self.rowlength-1):
					time.sleep(.5)
					self.port.write(".")
			for j in range(self.rowcount):
				self.writerow(j," ")
				for i in range(self.rowlength-1):
					time.sleep(.5)
					self.port.write(" ")
		return(0)

	def off(self):
		self.port.write(chr(254))		# cmd
		self.port.write(chr(8))		
		time.sleep(.2)

	def on(self):
		self.port.write(chr(254))		# cmd
		self.port.write(chr(12))		
		time.sleep(.2)
			
if __name__ == "__main__":
	print "Running oled class as a standalone app"
	logging.basicConfig(filename= LOGFILE,
						filemode='w',
						level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running oled class as a standalone app")
	myOled = Screen()
	dir(myOled)				# list functions for debug purposes
	myOled.cleardisplay()
	myOled.writerow(0,"   OLED class       ")
	myOled.writerow(1,"Config size="+str(myOled.rowlength)+"x"+str(myOled.rowcount))
	if myOled.rowcount > 2:
		myOled.writerow(2,"01234567890123456789")
		myOled.writerow(3,"Running oled.py     ")
#	myOled.screensave()
		
