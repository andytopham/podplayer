#!/usr/bin/python
'''Module to control mpd using the native python library python-mpd2. Imported by iradio.'''
import time
import datetime
import logging
import subprocess
import requests
import os
from bs4 import BeautifulSoup
import bbcradio
from mpd import MPDClient

class Mpc:
	'''Class: mpc - using native python. Uses bbcradio class.'''
	MP3DIR = "/var/lib/mpd/music/"
	STOPPED = 0
	PLAYING = 1
	VOLSTEP = 5
#	TIMEDOUT = 2	#	this is just the same as STOPPED
	STOPPEDPROGNAME = "                   ."
	PAUSE = 1
	UNPAUSE = 0
	
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.client = MPDClient()
		self.client.timeout = 10 # seconds
		self.client.idletimeout = None
		self.client.connect("localhost", 6600)
		self.client.clear()
		self.logger.info("python-mpd2 version:"+self.client.mpd_version)
		self.playState = self.STOPPED		# playing or stopped
		self.station = 0		# station number
		self.podnumber = 0
		self.podmode = 0
		self.podcount = 0
		self.stale_links = 0
		self.myBBC = bbcradio.bbcradio()
		self.logger.info("Loaded station count:"+str(self.myBBC.load()))
		self.updatedb()						# just run this occasionally
	
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
		'''Call the BBCradio routine to load the stations.'''
		if self.podmode == 0:		# only load the stations if we are in radio mode
			self.myBBC.load()
			self.play()
		else:
			self.stale_links = 1	# flag for later
		return(0)
		
	def switchmode(self):
		''' Toggle between radio and pod modes.'''
		self.logger.info("Switching mode")
		if self.podmode == 0:		# its radio mode now, so switch to pod mode
			self.logger.info("Going to pod mode, playing pod number "+str(self.podnumber))
			self.podmode = 1
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
			self.podcounter()
			self.client.play(1)
			self.lastplayed = self.client.currentsong()
			return(self.podnumber)
		else:						# switch to radio mode
			self.logger.info("Going to radio mode, playing station number "+str(self.station))
			self.podmode = 0
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
#		self.elapsedtime = self.elapsed()
		self.logger.info('Stop routine.')
		try:
			self.client.stop()
		except:
			self.logger.warning("Failed to send stop command.", exc_info=True)
		self.playState = self.STOPPED				# argh! this has to be this late, or it resets elapsed to zero!!
		return(0)
		
	def play(self):
		"""Send the play signal to mpc."""
		self.logger.info("Play: setting play.")
		if self.podmode == 0:
			self.logger.info("Selected station: "+str(self.station))
			try:
				self.client.play(self.station)
			except:
				self.logger.error("Failed to set play for radio station.")
		else:
			self.logger.info("Selected pod: "+str(self.podnumber))
			try:
				self.client.play(self.podnumber)
			except:
				self.logger.error("Failed to set play for podcast.")
		self.playState = self.PLAYING
		return(0)

	def pause(self):
		"""Send the pause signal to mpc."""
		self.logger.info("Pause.")
		if self.podmode == 0:
			self.logger.info("Selected station: "+str(self.station))
		else:
			self.logger.info("Selected pod: "+str(self.podnumber))
		if self.client.status()['state'] == 'pause':
			logging.error('mpd already paused.')
			return(1)
		try:
			self.client.pause(1)
		except:
			self.logger.error("Failed to pause playback.")
		self.playState = self.STOPPED
		return(0)

	def unpause(self):
		"""Send the unpause signal to mpc."""
		self.logger.info("Unpause.")
		if self.podmode == 0:
			self.logger.info("Selected station: "+str(self.station))
		else:
			self.logger.info("Selected pod: "+str(self.podnumber))
		if self.client.status()['state'] == 'play':
			logging.error('mpd already playing.')
			return(1)
		try:
			self.client.pause(0)
		except:
			self.logger.error("Failed to unpause playback.")
		self.playState = self.PLAYING
		return(0)
		
	def chgvol(self,vol):
		"""Send the change volume signal to mpc. python-mpd no longer supports chg volume."""
		self.logger.info("Chg vol: "+str(vol))
		if vol > 0:
			p = subprocess.check_output(['mpc', 'volume', '+'+str(self.VOLSTEP)])
		else:
			p = subprocess.check_output(['mpc', 'volume', str(-self.VOLSTEP)])
		line = p.splitlines()[2]
		vol,val = line.split()[0:2]
		print vol,val
		self.logger.info(vol+' '+val)
		return(0)
		
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
		if self.podmode == 1:
			self.deleteFile()			# get rid of the one just moved from
			self.podnumber += 1
			self.logger.info("Next podcast: moving to "+str(self.podnumber)+" out of "+str(self.podcount))
			if self.podnumber > self.podcount-1:
				self.podnumber = 0
				return(-1)				# finished pods
			self.client.play(self.podnumber)
			return(self.podnumber)
		else:						# its radio mode
			self.logger.info("Next radio station: moving to "+str(self.station+1)+" out of "+str(self.myBBC.stationcount()))
			self.station += 1
			if self.station > self.myBBC.stationcount()-1:
				self.station = 0
			self.play()
			return(self.station)
		
	def progname(self):
		"""Fetch the name of the currently playing programme or podcast."""
		if self.playState == self.STOPPED:
			self.logger.info("Fetching mpd program name for stopped program")
			return(self.STOPPEDPROGNAME)
		else:
			if self.podmode == 1:		# pod mode
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
			
	def audioTimeout(self):	
		if self.playState == self.PLAYING:
			self.logger.warning("Audio timeout")
			if self.podmode:
				self.pause()
			else:
				self.stop()
			return(0)
		else:
			return(0)

if __name__ == "__main__":
	'''mpc.py. Called if this file is called standalone. Then just runs a selftest. '''
#	print "Running mpc class as a standalone app"
	logging.basicConfig(filename='log/mpc.log',
						filemode='w',
						level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running mpc class as a standalone app")

	print __doc__
	print dir(Mpc)
	myMpc = Mpc()
	myMpc.play()
	myMpc.progname()

