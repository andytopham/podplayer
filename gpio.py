#!/usr/bin/python
''' Module to control the gpio switches.
	Imported by iradio.
	Will poll switches in a loop if called standalone.
	Slice of Pi pinout:
		Pin	Slice 	RPi/BCM	Use
		11	GP0		GPIO17	Next
		12	GP1		GPIO18	Stop
		13	GP2		GPIO21 	Volup
		15	GP3		GPIO22	Voldown
		16	GP4		GPIO23	-
		18	GP5		GPIO24
		22	GP6		GPIO25
		7	GP7		GPIO4
	RPi.GPIO lib is required for this class. To install gpio lib:
		sudo apt-get update
		sudo apt-get dist-upgrade
		sudo apt-get install python-rpi.gpio python3-rpi.gpio
'''
import RPi.GPIO as GPIO
import time, datetime, logging, subprocess
import timeout, infodisplay
from mpc2 import Mpc
from system import System
import config			# needed for the number of oled rows

BUTTONNONE = 0
BUTTONNEXT = 1
BUTTONSTOP = 2
BUTTONVOLUP = 3
BUTTONVOLDOWN = 4
BUTTONMODE = 5
BUTTONREBOOT = 6
BUTTONHALT = 7
PRESSED = False		# decides which edge the button works on
UPDATEOLEDFLAG = 1
UPDATETEMPERATUREFLAG = 2
UPDATESTATIONFLAG = 3
AUDIOTIMEOUTFLAG = 4
VOLUMETIMEOUTFLAG = 5
DISPLAYTIMEOUTFLAG = 6
SCROLL_ROW = 6

class Gpio:
	'''A class containing ways to handle the RPi gpio. '''
	def __init__(self):
		'''Initialise GPIO ports. '''
		self.logger = logging.getLogger(__name__)
		self.logger.info("Starting gpio class")
		#initialise the variables
		self.next = 0
		self.stop = 0
		self.vol = 0
		self.pod = 0
		self.chgvol_flag = 0
		self.setup()
		self.setupcallbacks()
		self.maxelapsed = 0
		self.button_pressed_time = datetime.datetime.now()

	def startup(self, verbosity):
		'''Initialisation for the objects that have variable startup behaviour'''
		self.myInfoDisplay = infodisplay.InfoDisplay()
		self.myMpc = Mpc()
		self.mySystem = System()
		host = self.mySystem.return_hostname()
		self.myInfoDisplay.writerow(1,host)
		self.myTimeout = timeout.Timeout(verbosity)
		self.programmename = self.myMpc.progname()
		remaining = self.myMpc.check_time_left()
		# First display set here
		self.myInfoDisplay.update_info_row(False)
		self.show_station()
		self.programmename = self.myMpc.progname()
		self.myInfoDisplay.show_prog_info(self.programmename)
	
	def master_loop(self):
		'''Continuously cycle through all the possible events.'''
		self.lasttime = time.time()		# has to be here to avoid long initial delay showing.
		while True:
			# regular events first
#			self.show_time_taken()
			if config.numberofrows == 2:
				time.sleep(.2)			# keep this inside try so that ctrl-c works here.		
				if self.chgvol_flag == 0:		# do not scroll the volume bar
					self.myInfoDisplay.scroll(SCROLL_ROW, self.programmename)
			try:
				self.process_timeouts()
				reboot = self.process_button_presses()
				if reboot == 1:
					GPIO.cleanup()
					return(1)
			except KeyboardInterrupt:
				print 'Keyboard interrupt'
				self.logger.warning('Keyboard interrupt')
				self.myInfoDisplay.writerow(1,'Keyboard stop.      ')
				self.myMpc.stop()
				GPIO.cleanup()
				return(1)
			except:			# all other errors - should never get here
				print 'Unknown error in master loop'
				self.myInfoDisplay.writerow(1,'Master loop err.')
				self.logger.error('Unknown error in master loop.')
				self.myMpc.stop()
				GPIO.cleanup()
				return(1)

	def show_time_taken(self):
		now = time.time()
		elapsed = now - self.lasttime
		if config.numberofrows > 2:
			self.myInfoDisplay.update_row3(elapsed,self.maxelapsed)
			if elapsed > self.maxelapsed:
				self.maxelapsed = elapsed
		self.lasttime = now
		return(0)
	
	def show_next_station(self):
		prog = self.myMpc.next_station()
		if config.numberofrows > 2:
#			self.myInfoDisplay.update_row4(prog)
			self.myInfoDisplay.writerow(1,'Station: {0:<16}'.format(prog))
		return(0)

	def show_station(self):
		prog = self.myMpc.this_station()
		if config.numberofrows > 2:
			self.myInfoDisplay.writerow(1,'Station: {0:<16}'.format(prog))
		return(0)
	
	def process_timeouts(self):
		'''Cases for each of the timeout types.'''
		try:
			self.chk_volume_timeout()
			timeout_type = self.myTimeout.checktimeouts()
			if timeout_type == 0:
				return(0)
			if timeout_type == VOLUMETIMEOUTFLAG:
				self.programmename = self.temp_progname
			if timeout_type == UPDATEOLEDFLAG:
	#			remaining = self.myTimeout.get_time_remaining()
				remaining = self.myMpc.check_time_left()
				self.myInfoDisplay.update_info_row(False)	# this has to be here to update time
				self.programmename = self.myMpc.progname()
			if timeout_type == UPDATETEMPERATUREFLAG:
				self.myInfoDisplay.update_info_row(True)
			if timeout_type == UPDATESTATIONFLAG:
				# handle the bbc links going stale
				if self.myMpc.loadbbc():			# failed
					time.sleep(1)					# wait to try again
					if self.myMpc.loadbbc():		# failed again
						return(1)
				self.myMpc.recover_playing()
				if self.mySystem.disk_usage():
					self.myInfoDisplay.writerow(1, 'Out of disk.')
					sys.exit()
				else:
					return(0)
			if timeout_type == AUDIOTIMEOUTFLAG:
				self.myMpc.audioTimeout()
				self.programmename = '    Timeout     '
			if timeout_type == DISPLAYTIMEOUTFLAG:
				a=1
				self.programmename = self.myMpc.progname()
				self.myInfoDisplay.show_prog_info(self.programmename)
		except:
			self.logger.warning('Error in process_timeouts. Timeout type:'+str(timeout_type))
			return(1)
		return(0)

	def chk_volume_timeout(self):
		'''Poll to see if the volume bar timeout has happened.'''
		if self.chgvol_flag == 1:
			try:
				if self.myTimeout.check_volume_timeout():
					self.chgvol_flag = 0
					self.programmename = self.temp_progname
			except:
				self.logger.info('Error in volume timeout handling')
		return(0)
		
	def process_button_presses(self):
		'''Poll for each of the button presses and return the new prog name.'''
		try:
			button = self.processbuttons()
			if button == 0:
				return(0)
			else:
				self.programmename = self.myMpc.progname()
				self.myTimeout.resetAudioTimeout()
				if button == BUTTONMODE:
					self.myMpc.switchmode()
				elif button == BUTTONNEXT:
					self.myInfoDisplay.writelabels(True)
					if self.myMpc.next() == -1:
						return('No pods left!')
					self.show_station()
					self.programmename = self.myMpc.progname()
					self.myInfoDisplay.show_prog_info(self.programmename)
					self.myInfoDisplay.writelabels()		# reset
				elif button == BUTTONSTOP:
					self.myInfoDisplay.writelabels(False, True)
					self.myMpc.toggle()
					self.programmename = self.myMpc.progname()
					self.myInfoDisplay.show_prog_info(self.programmename)
					self.myInfoDisplay.writelabels()		# reset
				elif button == BUTTONREBOOT:
					print 'Rebooting...'
					self.myMpc.stop()
					self.myInfoDisplay.writerow(1, 'Rebooting...     ')
					time.sleep(2)
					p = subprocess.call(['reboot'])
					return(1)
				elif button == BUTTONHALT:
					print 'Halting...'
					self.myMpc.stop()
					self.myInfoDisplay.writerow(1, 'Halting...      ')
					time.sleep(2)
					p = subprocess.call(['halt'])
					return(1)
				elif button == BUTTONVOLUP:
					v = self.myMpc.chgvol(+1)
					self.show_vol_bar(v)
				elif button == BUTTONVOLDOWN:
					v = self.myMpc.chgvol(-1)
					self.show_vol_bar(v)
		except:
			self.logger.warning('Error in process_button_presses: Value='+str(button))
			return(-1)
		return(0)
	
	def show_vol_bar(self, volume):
		'''Draw the volume bar on the display.'''
		self.logger.info('vol bar '+str(volume))
		self.chgvol_flag = 1
		try:
			self.myTimeout.setVolumeTimeout()
			self.temp_progname = self.programmename
			self.programmename = ''
			for i in range(0, int(volume), 5):		# add a char every 5%
				self.programmename += ">"
			self.programmename += "      "
			self.myInfoDisplay.displayvol(self.programmename)
		except:
			print ' trouble at t mill'
		return(0)
		
	def setup(self):
		'''Setup the gpio port.'''
		self.logger.info("def gpio setup")
		rev = GPIO.RPI_REVISION
		print 'RPi board revision: ',rev
		self.logger.info("RPi board revision:"+str(rev)
						+". RPi.GPIO revision:"+str(GPIO.VERSION)+".  ")
		# use P1 header pin numbering convention
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(True)
		GPIO.setup(config.NEXTSW, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
		GPIO.setup(config.STOPSW, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
		GPIO.setup(config.VOLUP, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
		GPIO.setup(config.VOLDOWN, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
		return()

	def pressednext(self,channel):
		'''Minimally manage the callback that is triggered when the Next button is pressed.'''
		self.logger.info("Button pressed next, Channel:"+str(channel))
		self.myTimeout.last_button_time()
		self.next = 1
		return(0)
		
	def pressedstop(self,channel):
		'''Minimally manage the callback that is triggered when the Stop button is pressed.'''
		self.logger.info("Button pressed stop, Channel:"+str(channel))
		self.myTimeout.last_button_time()
		self.stop = 1
		return(0)

	def pressedvolup(self,channel):
		'''Minimally manage the callback that is triggered when the volup button is pressed.'''
		self.logger.info("Button pressed volup, Channel:"+str(channel))
		self.myTimeout.last_button_time()
		self.vol = 1
		return(0)

	def pressedvoldown(self,channel):
		'''Minimally manage the callback that is triggered when the voldown button is pressed.'''
		self.logger.info("Button pressed voldown, Channel:"+str(channel))
		self.myTimeout.last_button_time()
		self.vol = -1
		return(0)
		
	def setupcallbacks(self):
		'''Setup gpio lib so that any button press will jump straight to the 
		callback processes listed above. This ensures that we get real responsiveness
		for button presses. Callbacks are run in a parallel process.'''
		self.logger.info("Using callbacks")
#		BOUNCETIME=100
		BOUNCETIME=200
		if PRESSED == True:
			GPIO.add_event_detect(config.NEXTSW, GPIO.RISING, callback=self.pressednext, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(config.STOPSW, GPIO.RISING, callback=self.pressedstop, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(config.VOLUP, GPIO.RISING, callback=self.pressedvolup, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(config.VOLDOWN, GPIO.RISING, callback=self.pressedvoldown, bouncetime=BOUNCETIME)
		else:
			GPIO.add_event_detect(config.NEXTSW, GPIO.FALLING, callback=self.pressednext, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(config.STOPSW, GPIO.FALLING, callback=self.pressedstop, bouncetime=BOUNCETIME)	
			GPIO.add_event_detect(config.VOLUP, GPIO.FALLING, callback=self.pressedvolup, bouncetime=BOUNCETIME)
			GPIO.add_event_detect(config.VOLDOWN, GPIO.FALLING, callback=self.pressedvoldown, bouncetime=BOUNCETIME)	
		
	def checkforstuckswitches(self):
		'''Check that the gpio switches are not stuck in one state.'''
		self.logger.debug("def gpio checkforstuckswitches")
		in17 = GPIO.input(config.NEXTSW)
		if in17 == self.PRESSED:
			self.logger.debug("pressed next sw")
			stuck = 1
			start = datetime.datetime.now()
			sofar = datetime.datetime.now()
			while sofar-start < datetime.timedelta(seconds=2):	# chk for 2 seconds
				sofar = datetime.datetime.now()
				in17 = GPIO.input(config.NEXTSW)
				if in17 != self.PRESSED:
					stuck = 0
			if stuck == 1:
				print "** Error: stuck next switch **"
				self.logger.error("Stuck next switch")
				return(stuck)
		in18 = GPIO.input(config.STOPSW)
		if in18 == self.PRESSED:
			stuck = 1
			start = datetime.datetime.now()
			sofar = datetime.datetime.now()
			while sofar-start < datetime.timedelta(seconds=2):	# chk for 2 seconds
				sofar = datetime.datetime.now()
				in18 = GPIO.input(config.STOPSW)
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
		in17 = GPIO.input(config.NEXTSW)
		if in17 == PRESSED:
			self.pod = 1
			return(1)
		return(0)

	def is_stop_held_down(self,delay):
		''' Call this after a delay after detecting the stop button is pressed.
			If the button is still pressed, then return 1. '''
		time.sleep(delay)
		in18 = GPIO.input(config.STOPSW)
		if in18 == PRESSED:
			self.reboot = 1
			return(1)
		return(0)
		
	def is_volup_held_down(self,delay):
		''' Call this after a delay after detecting the volup button is pressed.
			If the button is still pressed, then return 1. '''
		time.sleep(delay)
		if GPIO.input(config.VOLUP) == PRESSED:
			return(True)
		return(False)

	def is_voldown_held_down(self,delay):
		''' Call this after a delay after detecting the volup button is pressed.
			If the button is still pressed, then return 1. '''
		time.sleep(delay)
		if GPIO.input(config.VOLDOWN) == PRESSED:
			return(True)
		return(False)
		
	def _old_processbuttons(self):
		'''Not used anymore ***
		Called by the main program. Expects callback processes to have
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
			if self.is_stop_held_down(.5) == 0:
				self.logger.info("Button pressed stop")
				self.stop = 0
				button = BUTTONSTOP
			else:								# button still held down
				if True:
					self.logger.warning("Button pressed halt")
					self.stop = 0					# clear down the button press
					button = BUTTONHALT
				else:
					self.logger.warning("Button pressed reboot")
					self.stop = 0					# clear down the button press
					button = BUTTONREBOOT
		if self.vol == 1:
			self.logger.info("Button pressed vol up")
			self.vol=0
#			if self.is_volup_held_down(.01):
			button = BUTTONVOLUP
		if self.vol == -1:
			self.logger.info("Button pressed vol down")
			self.vol=0
			if self.is_voldown_held_down(.01):
				button = BUTTONVOLDOWN
		return(button)
		
	def processbuttons(self):
		'''Called by the main program. Expects callback processes to have
			already set the Next and Stop states.'''
		button=0
		if self.next == 1:
			self.logger.info("Button pressed next")
			self.next = 0
			button = BUTTONNEXT
		if self.stop == 1:
			self.logger.info("Button pressed stop")
			self.stop = 0
			button = BUTTONSTOP
		if self.vol == 1:
			self.logger.info("Button pressed vol up")
			self.vol=0
			button = BUTTONVOLUP
		if self.vol == -1:
			self.logger.info("Button pressed vol down")
			self.vol=0
			button = BUTTONVOLDOWN
#		self.logger.info("processbuttons: "+str(button))
		return(button)
			
	def _cleanup(self):
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
	
	def bounce_test(self):
		'''Print the time between the first two switch bounces.'''
		a = [17,18,21,22]
		for i in range(len(a)):
			GPIO.setup(a[i],GPIO.IN)
			print 'Testing input '+str(a[i])+', press when ready...'
			GPIO.setup(a[i],GPIO.IN)
			for j in range(3):
				t = GPIO.input(a[i])
				while t == GPIO.input(a[i]):		# wait for switch press
					pass
				s = GPIO.input(a[i])
				start = datetime.datetime.now()
				while s == GPIO.input(a[i]):		# timing until state changes
					pass
				end = datetime.datetime.now()		
				print end-start
		return(0)
	
if __name__ == "__main__":
	'''Called if this file is called standalone. Then just runs a selftest. '''
	logging.basicConfig(filename='log/gpio.log',
						filemode='w',
						level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running gpio class as a standalone app")
	myGpio = Gpio()
#	myGpio.setup()
	myGpio.bounce_test()
#	myGpio.scan()
#	myGpio.checkforstuckswitches()
