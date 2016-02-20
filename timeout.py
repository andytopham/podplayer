#!/usr/bin/python
'''Control a series of timeouts.'''

import time, datetime, logging

# Timeout values, all in minutes except where stated
OLEDTIMEOUT = 1
# TEMPERATURETIMEOUT = 15
# STATIONTIMEOUT = 240
AUDIOTIMEOUT = 45
VOLUMETIMEOUT = 4		# seconds
DISPLAYTIMEOUT = 120		# seconds

# verbose ones
VOLEDTIMEOUT = 1
# VTEMPERATURETIMEOUT = 15
# VSTATIONTIMEOUT = 240
VAUDIOTIMEOUT = 45
VVOLUMETIMEOUT = 4		# seconds
VDISPLAYTIMEOUT = 20

# Timeout flags
UPDATEOLEDFLAG = 1
# UPDATETEMPERATUREFLAG = 2
# UPDATESTATIONFLAG = 3
AUDIOTIMEOUTFLAG = 4
VOLUMETIMEOUTFLAG = 5
DISPLAYTIMEOUTFLAG = 6

class Timeout:
	def __init__(self, verbose=0):
		self.logger = logging.getLogger(__name__)
		self.logger.info('Setting timeouts: verbose='+str(verbose))
		if verbose == 1:
			self.logger.info('Timeouts(mins): OLED='+str(VOLEDTIMEOUT)
				+' AudioTimeout='+str(VAUDIOTIMEOUT))
			self.oledupdatefreq = datetime.timedelta(minutes=VOLEDTIMEOUT)
			self.audiotimeoutfreq = datetime.timedelta(minutes=VAUDIOTIMEOUT)
			self.volumetimeoutfreq = datetime.timedelta(seconds=VVOLUMETIMEOUT)
			self.displaytimeoutfreq = datetime.timedelta(seconds=DISPLAYTIMEOUT)
		else:
			self.logger.info('Timeouts(mins): OLED='+str(OLEDTIMEOUT)
				+' AudioTimeout='+str(AUDIOTIMEOUT))
			self.oledupdatefreq = datetime.timedelta(minutes=OLEDTIMEOUT)
			self.audiotimeoutfreq = datetime.timedelta(minutes=AUDIOTIMEOUT)
			self.volumetimeoutfreq = datetime.timedelta(seconds=VOLUMETIMEOUT)
			self.displaytimeoutfreq = datetime.timedelta(seconds=DISPLAYTIMEOUT)
		#initialise timers
		self.start = datetime.datetime.now()
		self.oledlastupdate = datetime.datetime.now()
		self.audiostart = datetime.datetime.now()
		self.volumestart = datetime.datetime.now()
		self.verbosity = verbose
		self.button_time = datetime.datetime.now()

	def checktimeouts(self):
		now = datetime.datetime.now()
		if (now - self.start) > self.oledupdatefreq:
			self.logger.info('Timeout: oled')
			self.start = datetime.datetime.now()
			return(UPDATEOLEDFLAG)
		if (now - self.audiostart) > self.audiotimeoutfreq:
			self.logger.warning('Audio timeout at '
								+datetime.datetime.now().strftime('%H:%M'))
			self.audiostart = datetime.datetime.now()
			return(AUDIOTIMEOUTFLAG)
		if (now - self.button_time) > self.displaytimeoutfreq:
			self.logger.info('Timeout: button press display')
			self.button_time = datetime.datetime.now()
#			self.recover_display()
			return(DISPLAYTIMEOUTFLAG)
		return(0)
		
	def resetAudioTimeout(self):
		self.audiostart = datetime.datetime.now()
	
	def setVolumeTimeout(self):
		self.volumestart = datetime.datetime.now()
		return(0)

	def check_volume_timeout(self):
#		self.logger.info('Check volume timeout. Timeout='+str(self.volumetimeoutfreq))
		now = datetime.datetime.now()
		if (now - self.volumestart) > self.volumetimeoutfreq:
			self.logger.info('Volume bar timeout')
			self.volumestart = datetime.datetime.now()
			return(1)
		return(0)
		
	def get_time_remaining(self):
		if self.verbosity == 0:
			return(0)
		now = datetime.datetime.now()
		try:
			x = now - self.audiostart
			mins = x.seconds // 60
		except:
			self.logger.warning('Cannot get time remaining mins.')
			mins = 99
#		self.logger.info('Time remaining: '+str(mins)+' minutes')
		return(mins)
		
	def last_button_time(self):
		'''Record the time the last button was pressed. Used for display timeout.'''
		self.button_time = datetime.datetime.now()
		return(0)