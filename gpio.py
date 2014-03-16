#!/usr/bin/python
''' 
	Module to control the gpio switches.
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
		Not the following...
		wget https://raspberry-gpio-python.googlecode.com/files/RPi.GPIO-0.5.2a.tar.gz
		tar zxf RPi.GPIO-0.5.2a.tar.gz
		cd RPi.GPIO-0.5.2a
		sudo python setup.py install
'''
import RPi.GPIO as GPIO
import time
import datetime
import logging
import config, timeout, oled, mpc2 as mpc, system

class gpio:
	'''A class containing ways to handle the RPi gpio. '''
	def __init__(self):
		'''Initialise GPIO ports. '''
		self.logger = logging.getLogger(__name__)
		self.logger.info("Starting gpio class")
		#start with some constants
		self.NEXTSW = 17
		self.STOPSW = 18
		self.VOLUP = 21
		self.VOLDOWN = 22
		self.YELLOWLED = 23					# temporary hack from 22
		self.REDLED = 24
		self.PRESSED = config.PRESSED			# True for small box, False for metal box
		#then initialise the variables
		self.next = 0
		self.stop = 0
		self.vol = 0
		self.pod = 0
		self.setup()
		self.setupcallbacks()
		self.myOled = oled.Oled()
		self.myMpc = mpc.Mpc()
		self.mySystem = system.System()

	def startup(self, verbosity):
		self.myTimeout = timeout.Timeout(verbosity)
		self.myOled.writerow(1, "podplayer v"+config.version+"      ")
		self.programmename = self.myMpc.progname()
	
	def master_loop(self):
		while True:
			# regular events first
			time.sleep(.2)
			self.myOled.scroll(self.programmename)
			self.process_timeouts()
			self.process_button_presses()
		
	def process_timeouts(self):
		'''Cases for each of the timeout types.'''
		timeout_type = self.myTimeout.checktimeouts()
		if timeout_type == 0:
			return(0)
		if timeout_type == config.UPDATEOLED:
			self.myOled.update_row2(0)		# this has to be here to update time
		if timeout_type == config.UPDATETEMPERATURE:
			self.myOled.update_row2(1)
		if timeout_type == config.UPDATESTATION:
			self.myMpc.loadbbc()						# handles the bbc links going stale
			if self.mySystem.disk_usage():
				self.myOled.writerow(1, 'Out of disk.')
				sys.exit()
			else:
				return(0)
		if timeout_type == config.AUDIOTIMEOUT:
			self.myMpc.audioTimeout()
			self.programmename = 'Timeout'
		return(0)

	def process_button_presses(self):
		'''Cases for each of the button presses and return the new prog name.'''
		button = self.processbuttons()
		if button == 0:
			return(0)
		else:
			self.myTimeout.resetAudioTimeout()
			if button == config.BUTTONMODE:
				self.myMpc.switchmode()
			elif button == config.BUTTONNEXT:
				if self.myMpc.next() == -1:
					return('No pods left!')
			elif button == config.BUTTONSTOP:
				self.myMpc.toggle()
			elif button == config.BUTTONVOLUP:
				self.myMpc.chgvol(+1)
			elif button == config.BUTTONVOLDOWN:
				self.myMpc.chgvol(-1)
			self.programmename = self.myMpc.progname()
			return(0)
	
	def setup(self):
		self.logger.debug("def gpio setup")
		self.logger.info("RPi board revision:"+str(GPIO.RPI_REVISION)+". RPi.GPIO revision:"+str(GPIO.VERSION)+".  ")
		# use P1 header pin numbering convention
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		#Fetch hw signature
		GPIO.setup(self.REDLED, GPIO.IN)		# temporary, normally output
		GPIO.setup(self.YELLOWLED, GPIO.IN)		# temporary, normally output
		a = [17,18,21,22,23,24,25,4]
		j = [0,0,0,0,0,0,0,0]
		for i in range(len(a)):
			GPIO.setup(a[i],GPIO.IN)
		for i in range(len(a)):
			j[i] = GPIO.input(a[i])
		if j[0] and j[1]:
			self.logger.info("HW type: partial")
			device = config.PARTIAL
		elif j[3]:
			self.logger.info("HW type: Humble")
			device = config.HUMBLE
		else:
			self.logger.info("HW type: full")
			device = config.FULL
		# Set up the GPIO channels - one input and one output
		GPIO.setup(self.NEXTSW, GPIO.IN)
		GPIO.setup(self.STOPSW, GPIO.IN)
		GPIO.setup(self.VOLUP, GPIO.IN)
		GPIO.setup(self.VOLDOWN, GPIO.IN)
		GPIO.setup(self.YELLOWLED, GPIO.OUT)		#yellow led
		GPIO.setup(self.REDLED, GPIO.OUT)		# red led
		GPIO.output(self.YELLOWLED, GPIO.HIGH)	# turn it off
		GPIO.output(self.REDLED, GPIO.LOW)	# turn it on
		return(device)

	def pressednext(self,channel):
		'''Minimally manage the callback that is triggered when the Next button is pressed.'''
		self.logger.info("Button pressed next, Channel:"+str(channel))
		self.next = 1
		return(0)
		
	def pressedstop(self,channel):
		'''Minimally manage the callback that is triggered when the Stop button is pressed.'''
#		self.logger.info("Button pressed stop, Channel:"+str(channel))
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
		if self.PRESSED == True:
			GPIO.add_event_detect(self.NEXTSW, GPIO.RISING, callback=self.pressednext, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(self.STOPSW, GPIO.RISING, callback=self.pressedstop, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(self.VOLUP, GPIO.RISING, callback=self.pressedvolup, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(self.VOLDOWN, GPIO.RISING, callback=self.pressedvoldown, bouncetime=BOUNCETIME)
		else:
			GPIO.add_event_detect(self.NEXTSW, GPIO.FALLING, callback=self.pressednext, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(self.STOPSW, GPIO.FALLING, callback=self.pressedstop, bouncetime=BOUNCETIME)	
			GPIO.add_event_detect(self.VOLUP, GPIO.FALLING, callback=self.pressedvolup, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(self.VOLDOWN, GPIO.FALLING, callback=self.pressedvoldown, bouncetime=BOUNCETIME)	
		
	def checkforstuckswitches(self):
		'''Run at power on to check that the switches are not stuck in one state.
			If this fails, then the calling program needs to exit.'''
		self.logger.debug("def gpio checkforstuckswitches")
		in17 = GPIO.input(self.NEXTSW)
		if in17 == self.PRESSED:
			self.logger.debug("pressed next sw")
			stuck = 1
			start = datetime.datetime.now()
			sofar = datetime.datetime.now()
			while sofar-start < datetime.timedelta(seconds=2):	# chk for 2 seconds
				sofar = datetime.datetime.now()
				in17 = GPIO.input(self.NEXTSW)
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
		in17 = GPIO.input(self.NEXTSW)
		if in17 == self.PRESSED:
			self.pod = 1
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
				button = config.BUTTONNEXT
			else:								# button still held down
				self.logger.info("Button pressed mode")
				self.next = 0							# clear down the button press
				button = config.BUTTONMODE			
		if self.stop == 1:
			self.logger.info("Button pressed stop")
			self.stop = 0
			button = config.BUTTONSTOP
		if self.vol == 1:
			self.logger.info("Button pressed vol up")
			self.vol=0
			button = config.BUTTONVOLUP
		if self.vol == -1:
			self.logger.info("Button pressed vol down")
			self.vol=0
			button = config.BUTTONVOLDOWN
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
		
	def test(self):
		'''Test routine. Loops and shows the status of the inputs and toggles outputs. '''
		print "Infinite loop:- press button to turn on led"
		self.logger.debug("def gpio test")
		while True:
			if GPIO.input(self.NEXTSW) == 1:
				GPIO.output(myGpio.YELLOWLED, GPIO.HIGH)
			else:
				GPIO.output(myGpio.YELLOWLED, GPIO.LOW)
			if GPIO.input(self.STOPSW) == 1:
				GPIO.output(myGpio.REDLED, GPIO.HIGH)
			else:
				GPIO.output(myGpio.REDLED, GPIO.LOW)
			
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
		a = [17,18,21,22,23,24,25,4]
		for i in range(len(a)):
			GPIO.setup(a[i],GPIO.IN)
			print a[i]," ",
		print
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
	myGpio = gpio()
	myGpio.setup()
	myGpio.scan()
	myGpio.checkforstuckswitches()
