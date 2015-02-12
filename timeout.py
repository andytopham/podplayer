#!/usr/bin/python
'''Control a series of timeouts.'''

import time, datetime, logging

# Timeout values, all in minutes
OLEDTIMEOUT = 1
TEMPERATURETIMEOUT = 15
STATIONTIMEOUT = 240
AUDIOTIMEOUT = 30
VOLUMETIMEOUT = 4		# seconds
# verbose ones
VOLEDTIMEOUT = 1
VTEMPERATURETIMEOUT = 15
VSTATIONTIMEOUT = 240
VAUDIOTIMEOUT = 30
VVOLUMETIMEOUT = 4		# seconds

# Timeout flags
UPDATEOLEDFLAG = 1
UPDATETEMPERATUREFLAG = 2
UPDATESTATIONFLAG = 3
AUDIOTIMEOUTFLAG = 4
VOLUMETIMEOUTFLAG = 5

class Timeout:
	def __init__(self, verbose=0):
		self.logger = logging.getLogger(__name__)
		self.logger.info('Setting timeouts: verbose='+str(verbose))
		if verbose == 1:
			self.logger.info('Timeouts(mins): OLED='+str(VOLEDTIMEOUT)
				+' Temperature='+str(VTEMPERATURETIMEOUT)
				+' Station='+str(VSTATIONTIMEOUT)
				+' AudioTimeout='+str(VAUDIOTIMEOUT))
			self.oledupdatefreq = datetime.timedelta(minutes=VOLEDTIMEOUT)
			self.temperatureupdatefreq = datetime.timedelta(minutes=VTEMPERATURETIMEOUT)
			self.stationupdatefreq = datetime.timedelta(minutes=VSTATIONTIMEOUT)	# a wild guess at how often the bbc change the key
			self.audiotimeoutfreq = datetime.timedelta(minutes=VAUDIOTIMEOUT)
			self.volumetimeoutfreq = datetime.timedelta(seconds=VVOLUMETIMEOUT)
		else:
			self.logger.info('Timeouts(mins): OLED='+str(OLEDTIMEOUT)
				+' Temperature='+str(TEMPERATURETIMEOUT)
				+' Station='+str(STATIONTIMEOUT)
				+' AudioTimeout='+str(AUDIOTIMEOUT))
			self.oledupdatefreq = datetime.timedelta(minutes=OLEDTIMEOUT)
			self.temperatureupdatefreq = datetime.timedelta(minutes=TEMPERATURETIMEOUT)
			self.stationupdatefreq = datetime.timedelta(minutes=STATIONTIMEOUT)	# a wild guess at how often the bbc change the key
			self.audiotimeoutfreq = datetime.timedelta(minutes=AUDIOTIMEOUT)
			self.volumetimeoutfreq = datetime.timedelta(seconds=VOLUMETIMEOUT)
		#initialise timers
		self.start = datetime.datetime.now()
		self.oledlastupdate = datetime.datetime.now()
		self.temperaturestart = datetime.datetime.now()
		self.stationstart = datetime.datetime.now()
		self.audiostart = datetime.datetime.now()
		self.volumestart = datetime.datetime.now()
		self.verbosity = verbose

	def checktimeouts(self):
		now = datetime.datetime.now()
		if (now - self.start) > self.oledupdatefreq:
			self.logger.info('Timeout: oled')
			self.start = datetime.datetime.now()
			return(UPDATEOLEDFLAG)
		if (now - self.temperaturestart) > self.temperatureupdatefreq:
			self.logger.info('Timeout: temperature')
			self.temperaturestart = datetime.datetime.now()
			return(UPDATETEMPERATUREFLAG)
		if (now - self.stationstart) > self.stationupdatefreq:
			self.logger.info('Timeout: station')
			self.stationstart = datetime.datetime.now()
			return(UPDATESTATIONFLAG)
		if (now - self.audiostart) > self.audiotimeoutfreq:
			self.logger.warning('Audio timeout at '
								+datetime.datetime.now().strftime('%H:%M'))
			self.audiostart = datetime.datetime.now()
			return(AUDIOTIMEOUTFLAG)
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
#			return(VOLUMETIMEOUTFLAG)
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
		