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

class mpc:
	'''Class: mpc - using native python. Uses bbcradio class.'''
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.client = MPDClient()
		self.client.timeout = 10 # seconds
		self.client.idletimeout = None
		self.client.connect("localhost", 6600)
		self.client.clear()
		self.logger.info("python-mpd2 version:"+self.client.mpd_version)
		self.playing = 0		# playing or stopped
		self.station = 0		# station number
		self.podnumber = 0
		self.VOLSTEP = 5
		self.podmode = 0
		self.podcount = 0
		self.elapsedtime = "0"
		self.lastplayed = ""
		self.timeout = 0
		self.stoppedprogname = "                   ."
		self.mp3dir = "/var/lib/mpd/music/"
		self.myBBC = bbcradio.bbcradio()
		self.logger.info("Loaded station count:"+str(self.myBBC.load2()))
		self.updatedb()						# just run this occassionally
		self.podcounter()
	
	def updatedb(self):
		'''Update the mpd db.'''
		self.logger.info("Updating db")
		try:
			self.client.update()
		except:
			self.logger.warning("Failed db update command")
		return(0)
		
#	def elapsed(self):
#		q = "0:0"
#		if self.playing == 1:
#			try:
#				self.client.status()
#				p = subprocess.check_output(["mpc"])
#				q = p.splitlines()[1].split()[2].split("/")[0]
#				self.logger.info("Elapsed time "+q)
#			except:
#				self.logger.warning("Failed to get elapsed time.")
#				q = "0:0"
#			try:
#				time.strptime(q,'%H:%M:%S')
#			except:
#				try:
#					time.strptime(q,'%M:%S')
#				except:
#					self.logger.warning("Will not parse as valid time: "+q+". Setting to 0.")	
#					q = "0"
#		return(q)
		
	def podcounter(self):
		''' Count how many podcasts exist in db. '''
		self.logger.info("Counting podcasts")
		try:
			i = self.client.status()
			self.podcount = int(i['playlistlength'])
			print "Number of podcasts = ",self.podcount
			self.logger.warning("Podcast count = "+str(self.podcount))
		except:
			self.logger.warning("Failed to count podcasts")
			self.podcount = 0
		return(self.podcount)
		
	def loadbbc(self):
		'''Call the BBCradio routine to load the stations.'''
		self.myBBC.load2()
		self.play()
		return(0)

#	def seek(self, timepoint):
#		self.logger.info("Seeking to "+timepoint)
#		try:
#			self.client.seekcur(timepoint)
#		except:
#			self.logger.warning("Failed to seek to timepoint: "+str(timepoint))
#		return(0)
		
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
				self.logger.info("Failed to clear list")
			try:
				d = self.client.list('file')
				for i in d:
					self.logger.info("Song added: "+i)
					self.client.add(i)
			except:
				self.logger.warning("Failed to add list")
			self.podcounter()
			self.client.play(1)
			self.seek(self.elapsedtime)
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
		self.logger.info("Deleting: "+self.mp3dir+filename)
		os.remove(self.mp3dir+filename)
		self.client.update()
		return(0)
		
	def cleanoldpods(self):
		''' Keep track of which files have been played. Delete files that have just finished. '''
		self.logger.info("Clean old pods")
		if self.playing == 1:
			if self.podmode == 1:							# playing podcasts
				try:										# handle occasional failures of mpc command.
					i = self.client.currentsong()
					current = i['album']
				except:
					current = self.lastplayed
					self.logger.warning("Failed to get current filename.")
				self.logger.info("CleanOldPods: Last one: "+str(self.lastplayed))
				self.logger.info("Latest: "+current+" "+str(self.elapsed()))
				if self.lastplayed == "":
					self.lastplayed = current
				else:
					if current != self.lastplayed:
						self.deletefile()
						self.lastplayed = current
		return(0)
				
	def stop(self):
		"""Send the stop signal to mpc."""
		self.elapsedtime = self.elapsed()
		self.logger.info("Stop at "+self.elapsedtime)
		try:
			self.client.stop()
		except:
			self.logger.warning("Failed to send stop command.")
		self.playing = 0				# argh! this has to be this late, or it resets elapsed to zero!!
		return(0)
		
	def play(self):
		"""Send the play signal to mpc."""
		self.logger.info("Play: setting play.")
		if self.podmode == 0:
			self.logger.info("Selected station: "+str(self.station))
			self.client.play(self.station)
		else:
			self.logger.info("Selected pod: "+str(self.podnumber))
			self.client.play(self.podnumber)
		# if we are coming back from timeout, might have lost track of station number after bbc station refresh
		self.playing = 1
		self.timeout = 0
		return(0)

	def pause(self):
		"""Send the play signal to mpc."""
		self.logger.info("Pause.")
		if self.podmode == 0:
			self.logger.info("Selected station: "+str(self.station))
			self.client.pause(1)
		else:
			self.logger.info("Selected pod: "+str(self.podnumber))
			self.client.pause(1)
		# if we are coming back from timeout, might have lost track of station number after bbc station refresh
		self.playing = 0
		self.timeout = 0
		return(0)

	def unpause(self):
		"""Send the play signal to mpc."""
		self.logger.info("Unpause.")
		if self.podmode == 0:
			self.logger.info("Selected station: "+str(self.station))
			self.client.pause(0)
		else:
			self.logger.info("Selected pod: "+str(self.podnumber))
			self.client.pause(0)
		# if we are coming back from timeout, might have lost track of station number after bbc station refresh
		self.playing = 1
		self.timeout = 0
		return(0)
		
	def chgvol(self,vol):
		"""Send the change volume signal to mpc. python-mpd no longer supports chg volume."""
		self.logger.info("Chg vol"+str(vol))
		if vol > 0:
			subprocess.call(['mpc', 'volume', '+'+str(self.VOLSTEP)])
		else:
			subprocess.call(['mpc', 'volume', str(-self.VOLSTEP)])
		return(0)
		
	def toggle(self):
		"""Toggle mpc mode between playing and stopped."""
		if self.playing == 1:
			self.logger.debug("Toggle: stopping")
			self.pause()
#			self.stop()
		else:
			self.logger.debug("Toggle: playing")
			self.unpause()
#			self.play()
		return(0)
		
	def prev(self):
		self.logger.info("Prev")
		self.client.previous()
		return(0)
		
	def deleteLastFile(self):
		'''Not used.'''
		i = self.client.status()
		id = i['songid']
		self.logger.info("Deleting pod:"+id)
		self.client.deleteid(id)
		self.podcounter()
		return(0)
		
	def next(self):
		"""Tell mpc to play the next item."""
		if self.podmode == 1:
			self.deleteFile()			# get rid of the one just moved from
			self.podnumber += 1
			self.logger.info("Next podcast: moving to "+str(self.podnumber)+" out of "+str(self.podcount))
			if self.podnumber > self.podcount-1:
				self.podnumber = 0
				return(0)				# finished pods
			self.client.play(self.podnumber)
			return(self.podnumber)
		else:						# its radio mode
			self.logger.info("Next radio station: moving to "+str(self.station+1)+" out of "+str(self.myBBC.stationcount))
			self.station += 1
			if self.station > self.myBBC.stationcount()-1:
				self.station = 0
			self.play()
			return(self.station)
		
	def progname(self):
		"""Fetch the name of the currently playing programme or podcast."""
		self.logger.info("Fetching mpd program name")
		if self.playing == 0:
			return(self.stoppedprogname)
		else:
			if self.podmode == 1:		# pod mode
				try:
					p = self.client.currentsong()
					progname = p['album']
					title = p['title']
					self.logger.info("Progname: "+progname)
				except:
					self.logger.info("Failed to get progname.")	
					progname = "   "
			else:						# radio mode
				progname = self.myBBC.stationname(self.station)
			print progname
			return(progname)
			
	def audioTimeout(self):	
		if self.playing == 1:
			self.logger.warning("Audio timeout")
			self.pause()
			self.timeout = 1
			return(0)
		else:
			return(0)

if __name__ == "__main__":
	'''mpc.py. Called if this file is called standalone. Then just runs a selftest. '''
#	print "Running mpc class as a standalone app"
	print __doc__
	logging.basicConfig(filename='log/mpc.log',
						filemode='w',
						level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running mpc class as a standalone app")

	myMpc = mpc()
	myMpc.play()
	myMpc.progname()

