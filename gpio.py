#!/usr/bin/python
# gpio.py
# All RPi gpio handling routines.

import RPi.GPIO as GPIO
import time, datetime, logging, subprocess, sys
import timeout, infodisplay
from mpc2 import Mpc
from system import System
import keys			# needed for the number of oled rows

BUTTONNONE = 0
BUTTONNEXT = 1
BUTTONSTOP = 2
BUTTONVOLUP = 3
BUTTONVOLDOWN = 4
BUTTONMODE = 5
BUTTONREBOOT = 6
BUTTONHALT = 7
UPDATEOLEDFLAG = 1
UPDATETEMPERATUREFLAG = 2
UPDATESTATIONFLAG = 3
AUDIOTIMEOUTFLAG = 4
VOLUMETIMEOUTFLAG = 5
DISPLAYTIMEOUTFLAG = 6
SCROLL_ROW = 6
# Positional index into pins array
NEXTSW = 0
STOPSW = 1
VOLUP =  2
VOLDOWN = 3
PODMODESW = 4
PREVSW = 5

class Gpio:
	'''A class containing ways to handle the RPi gpio. '''
	def __init__(self, board = 'oled2'):
		'''Initialise GPIO ports. '''
		self.logger = logging.getLogger(__name__)
		self.logger.info("Starting gpio class")
		board = keys.board
		if board == 'oled4':
			self.pins = [17,22,25,4,18,24]
		elif board == 'oled2':
			self.pins = [17,18,21,22,25,24]
		elif board == 'slice':
			self.pins = [17,18,21,22,23,24,25,4]		# slice of pi
		elif board == 'tft':
			self.pins = [19,4]							# tft
		elif board == 'uoled':
			self.pins = [17,18,21,22]		# not really, just for testing.
		else:
			self.logger.info('Error: switch definitions not included.')
			print 'Gpio error: board type not defined.'
			print 'Error: switch definitions not included.'
			raise InitError(0)		
		self.next = 0
		self.stop = 0
		self.vol = 0
		self.pod = 0
		self.chgvol_flag = 0
		self.setup()
		self.setupcallbacks()
		self.maxelapsed = 0
		self.button_pressed_time = datetime.datetime.now()

			
	def rpi_rev(self):
		return(GPIO.RPI_REVISION)
	
	def setup(self):
		'''Setup the gpio port.'''
		self.logger.info("def gpio setup")
		rev = self.rpi_rev()
		print 'RPi board revision: ',rev
		self.logger.info("RPi board revision:"+str(rev)
						+". RPi.GPIO revision:"+str(GPIO.VERSION)+".  ")
		# use P1 header pin numbering convention
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(True)
		GPIO.setup(self.pins[NEXTSW], GPIO.IN,  pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.pins[STOPSW], GPIO.IN,  pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.pins[VOLUP], GPIO.IN,  pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.pins[VOLDOWN], GPIO.IN,  pull_up_down=GPIO.PUD_UP)
		return()

	def pressednext(self,channel):
		'''Minimally manage the callback that is triggered when the Next button is pressed.'''
		self.logger.info("Button pressed next, Channel:"+str(channel))
		self.next = 1
		return(0)
		
	def pressedstop(self,channel):
		'''Minimally manage the callback that is triggered when the Stop button is pressed.'''
		self.logger.info("Button pressed stop, Channel:"+str(channel))
		self.stop = 1
		return(0)

	def pressedvolup(self,channel):
		'''Minimally manage the callback that is triggered when the volup button is pressed.'''
		self.logger.info("Button pressed volup, Channel:"+str(channel))
		self.vol = 1
		return(0)

	def pressedvoldown(self,channel):
		'''Minimally manage the callback that is triggered when the voldown button is pressed.'''
		self.logger.info("Button pressed voldown, Channel:"+str(channel))
		self.vol = -1
		return(0)
		
	def setupcallbacks(self):
		'''Setup gpio lib so that any button press will jump straight to the 
		callback processes listed above. This ensures that we get real responsiveness
		for button presses. Callbacks are run in a parallel process.'''
		self.logger.info("Using callbacks")
		BOUNCETIME=100
#		BOUNCETIME=20
		try:
			GPIO.add_event_detect(self.pins[NEXTSW], GPIO.FALLING, callback=self.pressednext, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(self.pins[STOPSW], GPIO.FALLING, callback=self.pressedstop, bouncetime=BOUNCETIME)	
			GPIO.add_event_detect(self.pins[VOLUP], GPIO.FALLING, callback=self.pressedvolup, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(self.pins[VOLDOWN], GPIO.FALLING, callback=self.pressedvoldown, bouncetime=BOUNCETIME)	
		except:
			self.logger.error('Failed to add edge detection. Must be run as root.')
			print 'Failed to add edge detection. Must be run as root.'
			return(1)
		return(0)
		
	def checkforstuckswitches(self):
		'''Check that the gpio switches are not stuck in one state.'''
		self.logger.debug("def gpio checkforstuckswitches")
		in17 = GPIO.input(self.pins[NEXTSW])
		if in17 == self.PRESSED:
			self.logger.debug("pressed next sw")
			stuck = 1
			start = datetime.datetime.now()
			sofar = datetime.datetime.now()
			while sofar-start < datetime.timedelta(seconds=2):	# chk for 2 seconds
				sofar = datetime.datetime.now()
				in17 = GPIO.input(self.pins[NEXTSW])
				if in17 != self.PRESSED:
					stuck = 0
			if stuck == 1:
				print "** Error: stuck next switch **"
				self.logger.error("Stuck next switch")
				return(stuck)
		in18 = GPIO.input(self.pins[STOPSW])
		if in18 == self.PRESSED:
			stuck = 1
			start = datetime.datetime.now()
			sofar = datetime.datetime.now()
			while sofar-start < datetime.timedelta(seconds=2):	# chk for 2 seconds
				sofar = datetime.datetime.now()
				in18 = GPIO.input(self.pins[STOPSW])
				if in18 != self.PRESSED:
					stuck = 0
			if stuck == 1:
				print "** Error: stuck stop switch **"
				self.logger.error("Stuck stop switch")
				return(stuck)
		return(0)
			
	def isnexthelddown(self,delay):
		''' Call this after a delay after detecting the next button is pressed.
			If the button is still pressed, then return 1. '''
		time.sleep(delay)
		in17 = GPIO.input(self.pins[NEXTSW])
		if in17 == PRESSED:
			self.pod = 1
			return(1)
		return(0)

	def is_stop_held_down(self,delay):
		''' Call this after a delay after detecting the stop button is pressed.
			If the button is still pressed, then return 1. '''
		time.sleep(delay)
		in18 = GPIO.input(self.pins[STOPSW])
		if in18 == PRESSED:
			self.reboot = 1
			return(1)
		return(0)
		
	def is_volup_held_down(self,delay):
		''' Call this after a delay after detecting the volup button is pressed.
			If the button is still pressed, then return 1. '''
		time.sleep(delay)
		if GPIO.input(self.pins[VOLUP]) == PRESSED:
			return(True)
		return(False)

	def is_voldown_held_down(self,delay):
		''' Call this after a delay after detecting the volup button is pressed.
			If the button is still pressed, then return 1. '''
		time.sleep(delay)
		if GPIO.input(self.pins[VOLDOWN]) == PRESSED:
			return(True)
		return(False)
				
	def cleanup(self):
		'''Not currently called. Should be called to tidily shutdown the gpio. '''
		# frees up the ports for another prog to use without warnings.
		GPIO.cleanup()
									
	def scan(self):
		'''Test routine to show current status of each gpio line.'''
		a = self.pins
		for i in range(len(a)):
			GPIO.setup(a[i],GPIO.IN, pull_up_down=GPIO.PUD_UP)
			print a[i]," ",
		print
#		print 'Next Stop Vol+ Vol- -    -    -    -'
		while True:
			for i in range(len(a)):
				print GPIO.input(a[i]),"  ",
			print
			time.sleep(1)

	def read(self):
		''' Return a list of the states of the current used inputs. Called by hwtest.py.'''
#		b = [0 for i in range(len(self.pins))]
		b = []
		for i in range(len(self.pins)):
			GPIO.setup(self.pins[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
		for i in range(len(self.pins)):
			b.append(GPIO.input(self.pins[i]))
		return(b)

	def bounce_test(self):
		'''Print the time between the first two switch bounces.'''
		a = self.pins
		SAMPLES = 20
		b = [0 for i in range(SAMPLES)]
		for i in range(len(a)):
			GPIO.setup(a[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
			time.sleep(1)		# settling time
			start = datetime.datetime.now()
			end = datetime.datetime.now()		
			print 'Time taken for consecutive reads of datetime.now', end-start
			start = datetime.datetime.now()
			GPIO.input(a[0])
			end = datetime.datetime.now()		
			print 'Time taken to read gpio input', end-start
			print 'Testing input '+str(a[i])+', press when ready...'
			for j in range(3):
				t = GPIO.input(a[i])
				while GPIO.input(a[i]) == 1:		# wait for switch press
					pass
				start = datetime.datetime.now()		# its been pressed, so start timer
				for k in range(SAMPLES):
					b[k] = GPIO.input(a[i])
				while GPIO.input(a[i]) == 0:		# wait for switch release
					pass
				end = datetime.datetime.now()		
				print end-start, b
		return(0)
		
	def callback_bounce_test(self):
		'''Print the time between the first two switch bounces.'''
		a = self.pins
		MEASUREMENTS = 5
		SAMPLES = 20
		b = [0 for i in range(SAMPLES)]
		for i in range(len(a)):
			GPIO.setup(a[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.remove_event_detect(a[i])
			GPIO.add_event_detect(a[i], GPIO.FALLING, callback=self.pushtest, bouncetime=1)
			start = datetime.datetime.now()
			end = datetime.datetime.now()		
			print 'Time taken for consecutive reads of datetime.now:', end-start
			start = datetime.datetime.now()
			GPIO.input(a[0])
			end = datetime.datetime.now()		
			print 'Time taken to read gpio input:                   ', end-start
			print 'Testing input '+str(a[i])+', press when ready...'
			for j in range(MEASUREMENTS):
				self.pressed = False
				while self.pressed == False:		# wait for switch press
					pass
				start = datetime.datetime.now()		# its been pressed, so start timer
				for k in range(SAMPLES):
					b[k] = GPIO.input(a[i])
				end = datetime.datetime.now()		
				print end-start, b
		return(0)
		
	def pushtest(self, channel):
		self.pressed = True
#		print 'Pressed', channel, '\n'
		return(0)
		
	def callback_bounce_no_polling_test(self):
		'''Print the time between the first two switch bounces.'''
		a = self.pins
		MEASUREMENTS = 5
		SAMPLES = 20
		b = [0 for i in range(SAMPLES)]
		for i in range(len(a)):
			GPIO.setup(a[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.remove_event_detect(a[i])
#			GPIO.add_event_detect(a[i], GPIO.BOTH, callback=self.fasttest, bouncetime=1)
			GPIO.add_event_detect(a[i], GPIO.BOTH, callback=self.fasttest)
			start = datetime.datetime.now()
			end = datetime.datetime.now()		
			print 'Time taken for consecutive reads of datetime.now:', end-start
			start = datetime.datetime.now()
			GPIO.input(a[0])
			end = datetime.datetime.now()		
			print 'Time taken to read gpio input:                   ', end-start
			print 'Testing input '+str(a[i])+', press when ready...'
			for j in range(MEASUREMENTS):
				self.pressed = False
				while self.pressed == False:		# wait for switch press
					pass
				start = datetime.datetime.now()		# its been pressed, so start timer
				self.pressed = False
				while self.pressed == True:		# wait for switch press
					pass
				end = datetime.datetime.now()		
				b[j] = end-start
#				print end-start, b
			print b
		return(0)
		
	def fasttest(self, channel):
		self.pressed = True
		return(0)
				
if __name__ == "__main__":
	'''Called if this file is called standalone. Then just runs a selftest. '''
	logging.basicConfig(filename='log/gpio.log',
						filemode='w',
						level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running gpio class as a standalone app")
	myGpio = Gpio()
#	myGpio.callback_bounce_test()
#	myGpio.callback_bounce_no_polling_test()
	myGpio.scan()
#	myGpio.checkforstuckswitches()
	myGpio.cleanup()
