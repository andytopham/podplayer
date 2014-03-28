#!/usr/bin/python
''' Load BBC radio stations into mpd.'''
import re
import subprocess
import time
import logging
import datetime
import requests
from bs4 import BeautifulSoup


class BBCradio:
	# These are the indicies to the url array.
	URLID = 0
	URLSTREAM = 1
	URLDETAILS = 2
	urls = [["BBCR2",	"r2_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_two" ],
			["BBCR4",	"r4_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_four" ],
			["BBCR4x",	"r4x_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_four_extra"],
			["BBCR5",	"r5l_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_five_live"],
			["BBCR6",	"r6_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_6music"]
			]
				
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.expiry_times = [None]*6
		__all__ = ['stationcount', 'load', 'stationname']		# list the functions available here

	def stationcount(self):
		'''Return the number of radio station urls.'''
		return(len(self.urls))
		
	def _refresh_pls_files(self):
		try:
			subprocess.Popen("rm -f *.pls", shell=True)		# need the -f to force removal of unwritable files
			q = subprocess.Popen('mpc -q clear', shell=True)
			q.wait()
		except:
			self.logger.error('Failed to clear old pls files.', exc_info=True)
			return(1)
		for i in self.urls:
			self.logger.info("Fetching: "+i[self.URLID])
			try:
				p = subprocess.Popen('wget -q http://www.bbc.co.uk/radio/listen/live/'
									+i[self.URLSTREAM], shell=True)
				p.wait()		# wait for last cmd to finish before we can read the file.
			except HTTPError, e:
				self.logger.error("Failed to fetch address for "+i[self.URLID], exc_info=True)
				return(1)
		return(0)
	
	def load(self, mpd_channel):
		'''Load the stations stored in the urls array. '''
		try:
			mpd_channel.connect("localhost", 6600)		# refresh the connection
		except:
			pass		# it must be already connected
		lines = []
		self.logger.warning("Getting BBC stations loaded")
		if self._refresh_pls_files():
			return(1)
		for i in self.urls:
			self.logger.info("Opening the stream file: "+i[self.URLSTREAM])
			try:
				source=open(i[self.URLSTREAM],'r')
				header = source.readline()				# this dumps first line of file
				if header != '[playlist]\n':
					print 'Invalid pls file contents:',t
					return(1)
				source.readline()		# NumberOfEntries=2
				file1 = source.readline()
				source.readline()		# Title1=No Title
				source.readline()		# Length1=-1
				file2 = source.readline()
				lines.append(file2)		# or, we could choose file1 - don't know difference
				source.close()	
			except:
				logging.warning("Could not open: "+i[self.URLSTREAM])
				return(1)
		for index, line in enumerate(lines):
			try:
				self.logger.info("Loading: "+line[6:])
				self._get_end_time(index, line[6:])
				mpd_channel.addid(line[6:].rstrip('\n'))
			except:
				self.logger.warning("Failed to add file to playlist: "+line[6:])
				return(1)
		self.logger.info('Loaded BBC stations.')
		print 'Loaded BBC stations.'
		return(0)
		
	def _get_end_time(self,i, link):
#		print link
		now = time.time()
		e = link.split('&e=')[1]
		end = float(e.split('&h=')[0])
		mins_left = int((end - now)/60)
		self.logger.info('Time left:'+str(mins_left))
		self.expiry_times[i] = end
		return(0)
		
	def check_time_left(self, station):
		now = time.time()
		end = self.expiry_times[station]
		mins_left = int((end - now)/60)
		self.logger.info('Time left:'+str(mins_left))
		return(mins_left)
		
	def _stationscanner(self):
		''' A test routine to find out how often the bbc updates the pls files.'''
		self.logger.info("Getting BBC stations loaded")		# refresh periodically
		subprocess.Popen("rm -f *.pls", shell=True)			# need the -f to force removal of unwritable files
		subprocess.Popen('mpc -q clear', shell=True)
		time.sleep(1)
		maxstation = self.stationcount()
		for string in self.bbcstation:
			self.logger.info("Fetching: "+string)
			try:
				p = subprocess.Popen('wget -q http://www.bbc.co.uk/radio/listen/live/'+string, shell=True)	# need to trap errors here.
				p.wait()		# need to wait for the last cmd to finish before we can read the file.
			except HTTPError, e:
				self.logger.error("Failed to fetch address for "+string)
				maxstation -= 1				# not as many as we planned
			else:
				source=open(string,'r')
				source.readline()		# this dumps first line of file
				source.readline()
				line=source.readline()
				source.close()			# do we need this??
				#print line[6:]
				print line[90:]

	def stationname(self, station):
		"""Fetch the name of the currently playing BBC programme."""
		self.logger.info("stationname: Fetching BBC radio program name")
		row = self.urls[station]
		address = row[self.URLDETAILS]
		try:
			soup = BeautifulSoup(requests.get(address).text)
		except requests.ConnectionError:
			self.logger.error("Connection error getting prog info")
			return("Connection error ")
		else:
			try:
				programmename = unicode(soup.title.string)
			except:
				programmename = "Unpronounceable"
			self.logger.info("Program name:"+programmename)
			return(programmename)
				
if __name__ == "__main__":
	print "Running bbcradio class as a standalone app"
	logging.basicConfig(filename='log/bbcradio.log',
						filemode='w',
						level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running bbcradio class as a standalone app")

	myBBC = bbcradio()
	myBBC._stationscanner()