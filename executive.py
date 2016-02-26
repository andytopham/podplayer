#!/usr/bin/python
# executive.py
# The main podplayer looping structure.

import time, datetime, logging, subprocess, sys
import infodisplay, keyboardpoller, gpio
from mpc2 import Mpc
from system import System
import threading
# import timeout

BUTTONNONE = 0
BUTTONNEXT = 1
BUTTONSTOP = 2
BUTTONVOLUP = 3
BUTTONVOLDOWN = 4
BUTTONMODE = 5
BUTTONREBOOT = 6
BUTTONHALT = 7
PRESSED = False		# decides which edge the button works on
AUDIOTIMEOUT = 60*45
DEBUGTIMEOUT = 90

class Executive:
	'''The main podplayer looping structure. '''
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.logger.info("Starting executive class")
		#initialise the variables
		self.die = False
		self.next = False
		self.stop = False
		self.volup = False
		self.voldown = False
		self.chgvol_flag = 0
		self.maxelapsed = 0
		self.error_string = ''
		
	def startup(self, verbosity):
		'''Initialisation for the objects that have variable startup behaviour'''
		self.myInfoDisplay = infodisplay.InfoDisplay()
		self.myKey = keyboardpoller.KeyboardPoller()
		self.myKey.start()
		self.myMpc = Mpc()
		try:
			self.myGpio = gpio.Gpio()
		except:
			self.cleanup('Failed to start gpio')
		self.mySystem = System()
		host = self.mySystem.return_hostname()
		self.myInfoDisplay.writerow(1,host)
		self.programmename = self.myMpc.progname()
		remaining = self.myMpc.check_time_left()
		self.myInfoDisplay.prog = self.myMpc.progname()
		self.myInfoDisplay.update_display()
		self.ending = False
		self.t = threading.Timer(AUDIOTIMEOUT, self.audiofunc)
		self.t.start()
		self.t.name = 'audiot'
		print threading.enumerate()		# helps debug
		self.dt = threading.Timer(DEBUGTIMEOUT, self.debugfunc)
#		self.dt.start()
		self.dt.name = 'debugt'
		
	def audiofunc(self):
		'''Called by the audio timeout Timer. Implements the actual timeout function.'''
		print 'Timeout'
		self.logger.info('Audio timeout')
		self.myInfoDisplay.writerow(0,'Timeout              ')
		self.myMpc.stop()
		self.myInfoDisplay.prog = 'Timeout               '
		return(0)

	def reset_audio_timer(self):
		'''Resets the audio timeout Timer. Called by each button push.'''
		self.t.cancel()
		time.sleep(1)
		if not self.ending:
			self.t = threading.Timer(AUDIOTIMEOUT, self.audiofunc)
			self.t.start()
			self.t.name = 'audiot'
	
	def debugfunc(self):
		'''Implements the actual timeout function.'''
		print 'Debug info...'
		print threading.enumerate()
		self.logger.info('Debug info')
		if not self.ending:
			self.dt = threading.Timer(DEBUGTIMEOUT, self.debugfunc)
			self.dt.start()
			self.dt.name = 'debugt'
		return(0)
	
	def cleanup(self, string):
		self.ending = True
		print 'Cleaning up:', string
		self.myInfoDisplay.t.cancel()	# stop updating the info row
		self.t.cancel()					# stop the audio timer
		self.dt.cancel					# stop the debug timer
		self.myInfoDisplay.clear()
		self.myInfoDisplay.writerow(0,string)
		self.myInfoDisplay.writerow(1, self.error_string)
		time.sleep(2)
		self.myInfoDisplay.cleanup()	# needed to stop weather polling.
		self.myKey.cleanup()
		self.logger.error(string)
		self.myMpc.cleanup()
		self.myGpio.cleanup()
		time.sleep(3)
		print threading.enumerate()		# should just show the main thread
		self.logger.warning('Finished exec cleanup')
		sys.exit(0)

	def chk_key(self):
		'''Act on keyboard presses.'''
		if self.myKey.command:
			self.myKey.command = False
			if self.myKey.exit:
				self.die = True
				self.myKey.exit = False
			if self.myKey.next:
				self.myKey.next = False
				self.next = True
			if self.myKey.stop:
				self.myKey.stop = False
				self.stop = True
			if self.myKey.volup:
				self.myKey.volup = False
				self.volup = True
			if self.myKey.voldown:
				self.myKey.voldown = False
				self.voldown = True
			return(True)
		else:
			return(False)
	
	def master_loop(self):
		'''Continuously cycle through all the possible events.'''
		self.lasttime = time.time()		# has to be here to avoid long initial delay showing.
		while True:
			self.chk_key()				# poll to see if there has been a key pressed
			try:
				if self.die == True:
					raise KeyboardInterrupt
				time.sleep(.2)			# keep this inside try so that ctrl-c works here.		
				reboot = self.process_button_presses()
				if reboot == 1:
					self.cleanup('Reboot')		# need to add to this!
			except KeyboardInterrupt:
				self.cleanup('Keyboard interrupt')
			except:			# all other errors - should never get here
				self.cleanup('Master loop error')

	def _show_time_taken(self):
		now = time.time()
		elapsed = now - self.lasttime
		self.myInfoDisplay.show_timings(elapsed,self.maxelapsed)
		if elapsed > self.maxelapsed:
			self.maxelapsed = elapsed
		self.lasttime = now
		return(0)
	
	def _show_next_station(self):
		prog = self.myMpc.next_station()
		self.myInfoDisplay.show_next_station(prog)
		return(0)
		
	def process_button_presses(self):
		'''Poll for each of the button presses and return the new prog name.'''
#		try:
		button = self._processbuttons()
		if button == 0:
			return(0)
		else:
			self.reset_audio_timer()				# reset audio timeout since button pressed
			if button == BUTTONMODE:
				self.myMpc.switchmode()
			elif button == BUTTONNEXT:
				self.myInfoDisplay.writelabels(True)
				if self.myMpc.next() == -1:
					return('No pods left!')
				prog = self.myMpc.progname()
				self.myInfoDisplay.show_prog_info(prog)
				self.myInfoDisplay.prog = prog	# displayed by background task
			elif button == BUTTONSTOP:
				self.myInfoDisplay.writelabels(False, True)
				self.myMpc.toggle()
				self.myInfoDisplay.show_prog_info(self.myMpc.progname())
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
#		except:
#			self.logger.warning('Error in process_button_presses: Value='+str(button))
#			return(-1)
		button = 0
		return(0)
		
	def _processbuttons(self):
		'''Called by process_button_presses. Expects callback processes to have
			already set the Next and Stop states.
			This routine is relatively quick. Slower parts are in the parent.'''
		button=0
		if self.myGpio.next or self.next:
			self.logger.info("Button pressed next")
			self.myGpio.next = False
			self.next = False
			button = BUTTONNEXT			
		if self.myGpio.stop or self.stop:
			self.logger.info("Button pressed stop")
			self.myGpio.stop = False
			self.stop = False
			button = BUTTONSTOP
		if (self.myGpio.vol == 1) or self.volup:
			self.logger.info("Button pressed vol up")
			self.myGpio.vol=0
			self.volup = False
			button = BUTTONVOLUP
		if (self.myGpio.vol == -1) or self.voldown:
			self.logger.info("Button pressed vol down")
			self.myGpio.vol=0
			self.voldown = False
			button = BUTTONVOLDOWN
#		self.logger.info("processbuttons: "+str(button))
		return(button)
			
	def _show_vol_bar(self, volume):
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
		
	def self_test(self):
		print 'Self test not yet implemented'
		return(0)
		
if __name__ == "__main__":
	'''Called if this file is called standalone. Then just runs a selftest. '''
	logging.basicConfig(filename='log/executive.log',
						filemode='w',
						level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running executive class as a standalone app")
	myExecutive = Executive()
	myExecutive.startup()
	myExecutive.self_test()
	# put some buttons here.....
	myExecutive.master_loop()
