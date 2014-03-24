#!/usr/bin/python
''' Module to control the gpio switches.
	Imported by iradio.
	Will poll switches in a loop if called standalone.
	Slice of Pi pinout:
		Pin	Slice 	RPi		Use
		11	GP0		GPIO17	SW1
		12	GP1		GPIO18	SW2
		13	GP2		GPIO21 	-
		15	GP3		GPIO22	yellow led
		16	GP4		GPIO23	-
		18	GP5		GPIO24	red led
		22	GP6		GPIO25
		7	GP7		GPIO4
	RPi.GPIO lib is required for this class. To install gpio lib:
		sudo apt-get update
		sudo apt-get dist-upgrade
		sudo apt-get install python-rpi.gpio python3-rpi.gpio
'''
import RPi.GPIO as GPIO
import time, datetime
import logging, subprocess
import timeout, infodisplay
from mpc2 import Mpc
from system import System

NEXTSW = 17
STOPSW = 18
VOLUP = 21
VOLDOWN = 22
BUTTONNONE = 0
BUTTONNEXT = 1
BUTTONSTOP = 2
BUTTONVOLUP = 3
BUTTONVOLDOWN = 4
BUTTONMODE = 5
BUTTONREBOOT = 6
UPDATEOLED = 1
UPDATETEMPERATURE = 2
UPDATESTATION = 3
AUDIOTIMEOUT = 4
PRESSED = False

class Gpio:
	'''A class containing ways to handle the RPi gpio. '''
	def __init__(self):
		'''Initialise GPIO ports. '''
		self.logger = logging.getLogger(__name__)
		self.logger.info("Starting gpio class")
		#start with some constants
#		self.NEXTSW = 17
#		self.STOPSW = 18
#		self.VOLUP = 21
#		self.VOLDOWN = 22
#		self.YELLOWLED = 23					# temporary hack from 22
#		self.REDLED = 24
#		self.PRESSED = config.PRESSED		# True for small box, False for metal box
		#then initialise the variables
		self.next = 0
		self.stop = 0
		self.vol = 0
		self.pod = 0
		self.setup()
		self.setupcallbacks()
		self.myInfoDisplay = infodisplay.InfoDisplay()
		self.myMpc = Mpc()
#		self.myMpc.start_mpd()
		self.mySystem = System()

	def startup(self, verbosity):
		self.myTimeout = timeout.Timeout(verbosity)
		self.programmename = self.myMpc.progname()
	
	def master_loop(self):
		while True:
			# regular events first
			time.sleep(.2)
			self.myInfoDisplay.scroll(self.programmename)
			self.process_timeouts()
			reboot = self.process_button_presses()
			if reboot == 1:
				return(1)
				
	def process_timeouts(self):
		'''Cases for each of the timeout types.'''
		timeout_type = self.myTimeout.checktimeouts()
		if timeout_type == 0:
			return(0)
		if timeout_type == UPDATEOLED:
			self.myInfoDisplay.update_row2(0)		# this has to be here to update time
		if timeout_type == UPDATETEMPERATURE:
			self.myInfoDisplay.update_row2(1)
		if timeout_type == UPDATESTATION:
			self.myMpc.loadbbc()						# handles the bbc links going stale
			if self.mySystem.disk_usage():
				self.myInfoDisplay.writerow(1, 'Out of disk.')
				sys.exit()
			else:
				return(0)
		if timeout_type == AUDIOTIMEOUT:
			self.myMpc.audioTimeout()
			self.programmename = '    Timeout     '
		return(0)

	def process_button_presses(self):
		'''Cases for each of the button presses and return the new prog name.'''
		button = self.processbuttons()
		if button == 0:
			return(0)
		else:
			self.myTimeout.resetAudioTimeout()
			if button == BUTTONMODE:
				self.myMpc.switchmode()
			elif button == BUTTONNEXT:
				if self.myMpc.next() == -1:
					return('No pods left!')
			elif button == BUTTONSTOP:
				self.myMpc.toggle()
			elif button == BUTTONREBOOT:
				print 'Rebooting...'
				self.myMpc.stop()
				self.myInfoDisplay.writerow(1, 'Rebooting...     ')
				time.sleep(2)
				p = subprocess.call(['reboot'])
				return(1)
			elif button == BUTTONVOLUP:
				self.myMpc.chgvol(+1)
			elif button == BUTTONVOLDOWN:
				self.myMpc.chgvol(-1)
			self.programmename = self.myMpc.progname()
			return(0)
	
	def setup(self):
		self.logger.debug("def gpio setup")
		self.logger.info("RPi board revision:"+str(GPIO.RPI_REVISION)+". RPi.GPIO revision:"+str(GPIO.VERSION)+".  ")
		# use P1 header pin numbering convention
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		a = [17,18,21,22,23,24,25,4]
		j = [0,0,0,0,0,0,0,0]
		for i in range(len(a)):
			GPIO.setup(a[i],GPIO.IN)
		GPIO.setup(NEXTSW, GPIO.IN)
		GPIO.setup(STOPSW, GPIO.IN)
		GPIO.setup(VOLUP, GPIO.IN)
		GPIO.setup(VOLDOWN, GPIO.IN)
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
		if PRESSED == True:
			GPIO.add_event_detect(NEXTSW, GPIO.RISING, callback=self.pressednext, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(STOPSW, GPIO.RISING, callback=self.pressedstop, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(VOLUP, GPIO.RISING, callback=self.pressedvolup, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(VOLDOWN, GPIO.RISING, callback=self.pressedvoldown, bouncetime=BOUNCETIME)
		else:
			GPIO.add_event_detect(NEXTSW, GPIO.FALLING, callback=self.pressednext, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(STOPSW, GPIO.FALLING, callback=self.pressedstop, bouncetime=BOUNCETIME)	
			GPIO.add_event_detect(VOLUP, GPIO.FALLING, callback=self.pressedvolup, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(VOLDOWN, GPIO.FALLING, callback=self.pressedvoldown, bouncetime=BOUNCETIME)	
		
	def checkforstuckswitches(self):
		'''Run at power on to check that the switches are not stuck in one state.
			If this fails, then the calling program needs to exit.'''
		self.logger.debug("def gpio checkforstuckswitches")
		in17 = GPIO.input(NEXTSW)
		if in17 == self.PRESSED:
			self.logger.debug("pressed next sw")
			stuck = 1
			start = datetime.datetime.now()
			sofar = datetime.datetime.now()
			while sofar-start < datetime.timedelta(seconds=2):	# chk for 2 seconds
				sofar = datetime.datetime.now()
				in17 = GPIO.input(NEXTSW)
				if in17 != self.PRESSED:
					stuck = 0
			if stuck == 1:
				print "** Error: stuck next switch **"
				self.logger.error("Stuck next switch")
				return(stuck)
		in18 = GPIO.input(self.STOPSW)
		if in18 == self.PRESSED:
			stuck = 1
			start = datetime.datetime.now()
			sofar = datetime.datetime.now()
			while sofar-start < datetime.timedelta(seconds=2):	# chk for 2 seconds
				sofar = datetime.datetime.now()
				in18 = GPIO.input(self.STOPSW)
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
		in17 = GPIO.input(NEXTSW)
		if in17 == PRESSED:
			self.pod = 1
			return(1)
		return(0)

	def is_stop_held_down(self,delay):
		''' Call this after a delay after detecting the stop button is pressed.
			If the button is still pressed, then return 1. '''
		time.sleep(delay)
		in18 = GPIO.input(STOPSW)
		if in18 == PRESSED:
			self.reboot = 1
			return(1)
		return(0)
		
	def processbuttons(self):
		'''Called by the main program. Expects callback processes to have
			already set the Next and Stop states.'''
		#self.logger.debug("def gpio processbuttons")
		button=0
		if self.next == 1:
			if self.isnexthelddown(.3) == 0:
				self.logger.info("Button pressed next")
				self.next = 0
				button = BUTTONNEXT
			else:								# button still held down
				self.logger.info("Button pressed mode")
				self.next = 0					# clear down the button press
				button = BUTTONMODE			
		if self.stop == 1:
			if self.is_stop_held_down(1) == 0:
				self.logger.info("Button pressed stop")
				self.stop = 0
				button = BUTTONSTOP
			else:								# button still held down
				self.logger.warning("Button pressed reboot")
				self.stop = 0					# clear down the button press
				button = BUTTONREBOOT
		if self.vol == 1:
			self.logger.info("Button pressed vol up")
			self.vol=0
			button = BUTTONVOLUP
		if self.vol == -1:
			self.logger.info("Button pressed vol down")
			self.vol=0
			button = BUTTONVOLDOWN
		return(button)

	def stopled(self,state):
		'''Test routine. Just changes led state based on button state. '''
		self.logger.info("Stop Led:"+str(state))
		if state == 0:
			GPIO.output(self.YELLOWLED, GPIO.HIGH)
		else:
			GPIO.output(self.YELLOWLED, GPIO.LOW)
		
	def nextled(self,state):
		'''Test routine. Just changes led state based on button state. '''
		self.logger.info("Next Led:"+str(state))
		if state == 0:
			GPIO.output(self.REDLED, GPIO.HIGH)
		else:
			GPIO.output(self.REDLED, GPIO.LOW)
			
	def cleanup(self):
		'''Not currently called. Should be called to tidily shutdown the gpio. '''
		# frees up the ports for another prog to use without warnings.
		GPIO.cleanup()
					
	def sequenceleds(self):
		'''Alternative test routine to be used with the clock3 slice of pi.'''
		self.logger.debug("def gpio sequenceleds")
		# This array is the Slice of Pi pins: GP0-7
		a = [17,18,21,22,23,24,25,4]
		for i in range(len(a)):
			GPIO.setup(a[i], GPIO.OUT)
		delay = .5
		while True:
			for i in range(len(a)):
				time.sleep(delay)
				print "High:",a[i]
				GPIO.output(a[i], GPIO.HIGH)
			for i in range(len(a)):
				time.sleep(delay)
				print "Low:",a[i]
				GPIO.output(a[i], GPIO.LOW)
				
	def scan(self):
		'''Test routine to show current status of each gpio line.'''
		a = [17,18,21,22,23,24,25,4]
		for i in range(len(a)):
			GPIO.setup(a[i],GPIO.IN)
			print a[i]," ",
		print
		print 'Next Stop Vol+ Vol- -    -    -    -'
		while True:
			for i in range(len(a)):
				print GPIO.input(a[i]),"  ",
			print
			time.sleep(1)
		
if __name__ == "__main__":
	'''Called if this file is called standalone. Then just runs a selftest. '''
	logging.basicConfig(filename='log/gpio.log',
						filemode='w',
						level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running gpio class as a standalone app")
	myGpio = Gpio()
	myGpio.setup()
	myGpio.scan()
	myGpio.checkforstuckswitches()
