#!/usr/bin/python
'''Module to control mpd using the native python library python-mpd2.'''
# Installation instructions for hifiberry....
# https://support.hifiberry.com/hc/en-us/articles/205377651-Configuring-Linux-4-x-or-higher

import time, datetime, logging, subprocess, requests, os
from bs4 import BeautifulSoup
from bbcradio import BBCradio
import mpd
# import pdb
# from mpd import MPDClient

RENEWALTIME = 15		# minutes until stream times out
#RENEWALTIME = 114		# minutes until stream times out - for debug

class Mpc:
	'''Class: mpc - using native python. Uses bbcradio class.'''
	MP3DIR = "/var/lib/mpd/music/"
	STOPPED = 0
	PLAYING = 1
	VOLSTEP = 5
	STOPPEDPROGNAME = "  Stopped              "
	
	def __init__(self, test_mode = False):
		self.logger = logging.getLogger(__name__)
		self.playState = self.STOPPED		# playing or stopped
		self.station = 0					# station number
		self.podnumber = 0
		self.podmode = False 
		self.podcount = 0
		self.stale_links = 0
		self. logger.info('Starting mpd client.')
		self.client = mpd.MPDClient()
		self.client.timeout = 10 # seconds
		self.client.idletimeout = None
		self.client.connect("localhost", 6600)
		self.client.clear()
		self.logger.info("python-mpd2 version:"+self.client.mpd_version)
		if test_mode:
			self.myBBC = BBCradio(self.client, 5)
		else:		# normal mode
			self.myBBC = BBCradio(self.client)
		self.myBBC.start()
		self.myBBC.stationname()		# this starts the perpetual loop collecting the names!
		self.updatedb()						# just run this occasionally
		self.setvol(40)
		self.station = 0
		while self.myBBC.stationcount == 0:	# wait for the first station to be ready
			time.sleep(1)
		self.play()

	def _start_mpd(self):
		self. logger.info('Starting mpd client.')
		self.client = mpd.MPDClient()
		self.client.timeout = 10 # seconds
		self.client.idletimeout = None
		self.client.connect("localhost", 6600)
		self.client.clear()
		self.logger.info("python-mpd2 version:"+self.client.mpd_version)
		self.updatedb()						# just run this occasionally
		print 'mpd connected'
		return(0)
		
	def chk_station_load(self):
		return(self.myBBC.load_error)
		
	def cleanup(self):
		self.stop()
		self.myBBC.cleanup()
		
	def next_station(self):
		no_of_stations = self.myBBC.stationcounter()
		self.logger.info("Show next radio station: "+str(self.station+1)+" out of "+str(no_of_stations))
		number = self.station + 1
		if number > no_of_stations - 1:
			number = 0
		line = self.myBBC.newurls[number]
		return(line[0])
		
	def this_station(self):
		'''The short identifier from my url list, not the full prog info.'''
		return(self.myBBC.newurls[self.station][0])
		
	def check_time_left(self):
		mins_left = self.myBBC.check_time_left(self.station)
		if mins_left < RENEWALTIME:
			print 'Time is running out - reloading bbc...'
			self.logger.warning('BBC token timeout, reloading stations.')
			self.loadbbc()
		return(mins_left)
		
	def updatedb(self):
		'''Update the mpd db.'''
		self.logger.info("Updating db")
		try:
			self.client.update()
		except:
			self.logger.warning("Failed db update command")
		return(0)
				
	def podcounter(self):
		''' Count how many podcasts exist in db. '''
		self.logger.info("Counting podcasts")
		try:
			i = self.client.status()
			self.podcount = int(i['playlistlength'])
			print "Number of podcasts = ",self.podcount
			self.logger.warning("Podcast count = "+str(self.podcount))
		except:
			self.logger.warning("Failed to count podcasts", exc_info=True)
			self.podcount = 0
		return(self.podcount)
		
	def loadbbc(self):
		'''Call the BBCradio routine to load the stations. 
		Sleeps are since bbc does not seem to respond well if we are too quick.'''
		if self.podmode == False:		# only load the stations if we are in radio mode
			time.sleep(1)
			if self.myBBC.load(self.client):
				print 'Failed to load BBC stations, trying again....'
				self.logger.warning('Failed to load BBC stations, trying again....')
				time.sleep(1)
				if self.myBBC.load(self.client) == -1:
					print 'Failed to load BBC stations again.'
					self.logger.warning('Failed to load BBC stations again.')
					return(1)
		else:
			self.stale_links = 1	# flag for later
		if self.playState == self.PLAYING:
			self.play()
		return(0)
		
	def switchmode(self):
		''' Toggle between radio and pod modes.'''
		self.logger.info("Switching mode")
		if self.podmode == False:		# its radio mode now, so switch to pod mode
			self.logger.info("Going to pod mode, playing pod number "+str(self.podnumber))
			self.podmode = True
			self.client.consume(1)
			try:
				self.client.clear()
			except:
				self.logger.info("Failed to clear list", exc_info=True)
			try:
				d = self.client.list('file')
				for i in d:
					self.logger.info("Song added: "+i)
					self.client.add(i)
			except:
				self.logger.warning("Failed to add list", exc_info=True)
			if self.podcounter() == 0:
				print "No podcasts left, switching to radio."
				self.switchmode()
				return(0)
			self.client.play(self.podnumber)
			self.lastplayed = self.client.currentsong()
			return(self.podnumber)
		else:						# switch to radio mode
			self.logger.info("Going to radio mode, playing station number "+str(self.station))
			self.podmode = False
			self.client.consume = 0
			self.client.clear()
			self.loadbbc()
			self.play()
		return(self.station)
	
	def deleteFile(self):
		'''Delete the mp3 that is currently playing and update db.'''
		i = self.client.currentsong()
		filename = i['file']
		try:
			self.logger.info("Deleting: "+self.MP3DIR+filename)
			os.remove(self.MP3DIR+filename)
		except:
			print "Failed to delete file."
			self.logger.warning('Failed to delete file.'+str(filename))
			st = os.stat(self.MP3DIR+filename)
			print 'Stat: ',st.st_mtime
		self.client.update()
		return(0)
				
	def stop(self):
		"""Send the stop signal to mpc."""
		self.logger.info('Stop routine.')
		try:
			self.client.stop()
		except mpd.ConnectionError:
			self.logger.warning('Stop: mpd connection error.')
			try:
				self.client.connect("localhost", 6600)
				self.client.stop()
			except:
				self.logger.warning("Failed to send stop command again.", exc_info=True)
				return(1)
		except:
			self.logger.warning("Failed to send stop command, unknown error.", exc_info=True)
			time.sleep(1)
			self.logger.warning("Trying again, reconnecting first.....")
			try:
				self.client.connect("localhost", 6600)
				self.client.stop()
			except:
				self.logger.warning("Failed to send stop command again.", exc_info=True)
				return(1)
		self.playState = self.STOPPED		# argh! this has to be this late, or it resets elapsed to zero!!
		return(0)
		
	def recover_playing(self):
		'''When we reload the stations, we need to restart playing if appropriate.'''
		if self.playState == self.PLAYING:
			self.play()
		return(0)
		
	def play(self):
		"""Send the play signal to mpc."""
		self.logger.info("Play: setting play.")
		if self.podmode == False:
			self.logger.info("Selected station: "+str(self.station))
			try:
				self.client.play(self.station)
			except mpd.ConnectionError:
				self.logger.warning('Play: mpd connection error.')
				try:
					self.client.connect("localhost", 6600)
					self.client.play(self.station)
				except:
					self.logger.warning("Failed to send play command again.", exc_info=True)
					raise
					return(1)
			except:
				self.logger.error("Failed to set play for radio station.")
				raise
		else:		# pod mode
			self.logger.info("Selected pod: "+str(self.podnumber))
			try:
				self.client.play(self.podnumber)
			except:
				self.logger.error("Failed to set play for podcast.")
		time.sleep(.1)
		try:
			time.sleep(1)
			p = self.client.currentsong()		# this is catching the old current song!!!!
		except:
			self.logger.error('Failed to fetch currentsong after play.')
			print 'No current song after play'
		self.playState = self.PLAYING
		return(0)

	def pause(self):
		"""Send the pause signal to mpc."""
		self.logger.info("Pause.")
		if self.podmode:
			self.logger.info("Selected pod: "+str(self.podnumber))
		else:
			self.logger.info("Selected station: "+str(self.station))
		if self.client.status()['state'] == 'pause':
			logging.error('mpd already paused.')
			return(1)
		try:
			self.client.pause(1)
		except MPDClient.ConnectionError:
			self.logger.warning('mpd connection error.')
			try:
				self.client.connect("localhost", 6600)
				self.client.pause(1)
			except:
				self.logger.warning("Failed to send pause command again.", exc_info=True)
				return(1)
		except:
			self.logger.error("Failed to pause playback.")
		self.playState = self.STOPPED
		return(0)

	def unpause(self):
		"""Send the unpause signal to mpc."""
		self.logger.info("Unpause.")
		if self.podmode:
			self.logger.info("Selected pod: "+str(self.podnumber))
		else:
			self.logger.info("Selected station: "+str(self.station))
		if self.client.status()['state'] == 'play':
			logging.error('mpd already playing.')
			return(1)
		try:
			self.client.pause(0)
		except MPDClient.ConnectionError:
			self.logger.warning('mpd connection error.')
			try:
				self.client.connect("localhost", 6600)
				self.client.pause(0)
			except:
				self.logger.warning("Failed to send unpause command again.", exc_info=True)
				return(1)
		except:
			self.logger.error("Failed to unpause playback.")
		self.playState = self.PLAYING
		return(0)
		
	def setvol(self,vol):
		"""Set the volume."""
		self.logger.info("Set vol: "+str(vol))
		p = subprocess.check_output(['mpc', 'volume', str(vol)])
#		line = p.splitlines()[2]			# fetch 3rd line
#		vol,val = line.split()[0:2]
		vol,val = p.split()[0:2]
		print vol,val
		self.logger.info(vol+' '+val)
		return(val.strip('%'))

	def chgvol(self,vol):
		"""Send the change volume signal to mpc. python-mpd no longer supports chg volume."""
		self.logger.info("Chg vol: "+str(vol))
		if vol > 0:
			p = subprocess.check_output(['mpc', 'volume', '+'+str(self.VOLSTEP)])
		else:
			p = subprocess.check_output(['mpc', 'volume', str(-self.VOLSTEP)])
		line = p.splitlines()[2]			# fetch 3rd line
		vol,val = line.split()[0:2]
		print vol,val
		self.logger.info(vol+' '+val)
		return(val.strip('%'))
			
	def toggle(self):
		"""Toggle mpc mode between playing and stopped."""
		if self.playState == self.PLAYING:
			self.logger.info("Toggle: stopping")
			if self.podmode:
				self.pause()
			else:
				self.stop()
		else:			# stopped
			self.logger.debug("Toggle: going to playing state")
			if self.podmode:
				self.unpause()
			else:
				self.play()
		return(0)
		
	def _prev(self):
		self.logger.info("Prev")
		self.client.previous()
		return(0)
		
	def next(self):
		"""Tell mpc to play the next item."""
		self.podmode = False
		if self.podmode:
			self.deleteFile()			# get rid of the one just moved from
			self.podnumber += 1
			self.logger.info("Next podcast: moving to "+str(self.podnumber)+" out of "+str(self.podcount))
			if self.podnumber > self.podcount-1:
				self.podnumber = 0
				return(-1)				# finished pods
			self.client.play(self.podnumber)
			return(self.podnumber)
		else:						# its radio mode
			self.station = self.station + 1
			if self.station > self.myBBC.stationcounter()-1:
				self.station = 0
			self.logger.info("Next: moving to station "+str(self.station))
			try:
				self.client.play(self.station)
			except mpd.ConnectionError:
				self.logger.warning('Next: mpd connection error.')
			return(self.station)

	def progname(self):
		if self.playState == self.STOPPED:
			return(self.STOPPEDPROGNAME)
		else:
			return(self.myBBC.bbcname[self.station])
	
	def oldprogname(self):
		"""Fetch the name of the currently playing programme or podcast."""
		if self.playState == self.STOPPED:
			self.logger.info("Fetching mpd program name for stopped program")
			return(self.STOPPEDPROGNAME)
		else:
			if self.podmode:		# pod mode
				self.logger.info("Fetching mpd pod name")
				try:
					p = self.client.currentsong()
					key_list = p.keys()
					album = ''
					if 'album' in key_list:
						album = p['album']
					elif 'artist' in key_list:
						album = p['artist']
					if 'title' in key_list:
						title = p['title']
					elif 'file' in key_list:
						title = p['file']
					posn = p['pos']			# the track number in the playlist
					date = p['last-modified']
					self.logger.info("Progname: "+album+' - '+title)
					progname = album+' - '+title
#					print progname+'-'+date
				except:
					self.logger.info("Failed to get progname.", exc_info=True)	
					progname = "No pod name.   "
			else:						# radio mode
				self.logger.info("Fetching mpd radio program name for station "+str(self.station)+': '+self.myBBC.urls[self.station][0])
				try:
					p = self.client.currentsong()
#					name = p['name']
					posn = p['pos']			# the track number in the playlist
					if int(posn) != self.station:
						self.logger.error("Station number out of sync. Local:"+str(self.station)+". Remote:"+posn)
#					self.logger.info("Progname: "+' - '+name)
#					progname = name
				except:
					self.logger.info("Failed to get progname for radio station.", exc_info=True)	
					progname = "No radio name.   "
				progname = self.myBBC.stationname(self.station)	#oldway of doing it
		return(progname)
			
if __name__ == "__main__":
	'''mpc.py. Called if this file is called standalone. Then just runs a selftest. '''
#	print "Running mpc class as a standalone app"
	logging.basicConfig(filename='log/mpc.log', filemode='w', level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running mpc class as a standalone app")

	print 'My mpc test prog'
	myMpc = Mpc(True)		# set test mode on
	myMpc.play()
	time.sleep(2)
	print 'Getting prog name'
	print myMpc.progname()
	time.sleep(2)
	print 'Stopping'
	myMpc.toggle()
	time.sleep(2)
	print 'Starting'
	myMpc.toggle()	
	time.sleep(4)
	print 'Now loop 5 times.'
	for i in range(5):
		print 'Next station'
		myMpc.next()
		print myMpc.progname()	
		time.sleep(4)
#	time.sleep(5)
	print 'Exiting main prog.'
	myMpc.cleanup()
	
	

