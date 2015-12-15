#!/usr/bin/python
# executive.py
# The main podplayer looping structure.

# import RPi.GPIO as GPIO
import time, datetime, logging, subprocess
import timeout, infodisplay
from mpc2 import Mpc
from system import System
import gpio
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

class Executive:
	'''The main podplayer looping structure. '''
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.logger.info("Starting executive class")
		#initialise the variables
		self.next = 0
		self.stop = 0
		self.vol = 0
		self.pod = 0
		self.chgvol_flag = 0
#		self.setup()
#		self.setupcallbacks()
		self.maxelapsed = 0
		self.button_pressed_time = datetime.datetime.now()

	def startup(self, verbosity):
		'''Initialisation for the objects that have variable startup behaviour'''
		self.myInfoDisplay = infodisplay.InfoDisplay()
		self.myMpc = Mpc()
		self.mySystem = System()
		self.myGpio = gpio.Gpio()
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
			if self.myInfoDisplay.rowcount < 3:
				self.myInfoDisplay.scroll(0,self.programmename)
				time.sleep(.2)			# keep this inside try so that ctrl-c works here.		
			try:
				self.process_timeouts()
				reboot = self.process_button_presses()
				if reboot == 1:
					self.myGpio.cleanup()
					return(1)
			except KeyboardInterrupt:
				print 'Keyboard interrupt'
				self.logger.warning('Keyboard interrupt')
				self.myInfoDisplay.writerow(1,'Keyboard stop.      ')
				self.myMpc.stop()
				self.myGpio.cleanup()
				return(1)
			except:			# all other errors - should never get here
				print 'Unknown error in master loop'
				self.myInfoDisplay.writerow(0,'Master loop err.')
				self.logger.error('Unknown error in master loop.')
				self.myMpc.stop()
				self.myGpio.cleanup()
				return(1)

	def show_time_taken(self):
		now = time.time()
		elapsed = now - self.lasttime
		self.myInfoDisplay.show_timings(elapsed,self.maxelapsed)
		if elapsed > self.maxelapsed:
			self.maxelapsed = elapsed
		self.lasttime = now
		return(0)
	
	def show_next_station(self):
		prog = self.myMpc.next_station()
		self.myInfoDisplay.show_next_station(prog)
		return(0)

	def show_station(self):
		prog = self.myMpc.this_station()
		self.myInfoDisplay.show_prog_info(prog)
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
			self.logger.error('Error in process_timeouts. Timeout type:'+str(timeout_type))
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
				self.myTimeout.last_button_time()
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
		
	def processbuttons(self):
		'''Called by the main program. Expects callback processes to have
			already set the Next and Stop states.'''
		button=0
		if self.myGpio.next == 1:
			self.logger.info("Button pressed next")
			self.myGpio.next = 0
			button = BUTTONNEXT
		if self.myGpio.stop == 1:
			self.logger.info("Button pressed stop")
			self.myGpio.stop = 0
			button = BUTTONSTOP
		if self.myGpio.vol == 1:
			self.logger.info("Button pressed vol up")
			self.myGpio.vol=0
			button = BUTTONVOLUP
		if self.myGpio.vol == -1:
			self.logger.info("Button pressed vol down")
			self.myGpio.vol=0
			button = BUTTONVOLDOWN
#		self.logger.info("processbuttons: "+str(button))
		return(button)
			
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
	myExecutive.self_test()
