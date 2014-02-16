#!/usr/bin/python
''' 
  Module to load BBC radio stations.
  Imported by mpc and thence by iradio.
  Methods:
	init
	stationcount
	selectstation(station)
	load2
	
'''
import re
import subprocess
import time
import logging
import datetime
import requests
from bs4 import BeautifulSoup

class bbcradio:
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.urls = [["BBCR2",	"r2_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_two" ],
					["BBCR4",	"r4_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_four" ],
					["BBCR4x",	"r4x_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_four_extra"],
					["BBCR5",	"r5l_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_five_live"],
					["BBCR6",	"r6_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_6music"]
					]
		# These are the indicies to the above array.
		self.URLID = 0
		self.URLSTREAM = 1
		self.URLDETAILS = 2

	def stationcount(self):
		return(len(self.urls))
		
#	def selectstation(self,station):
#		if upbuttonpressed == True:
#			if station < maxstation:
#				station += 1
#			else:
#				station = 0
#		if downbuttonpressed == True:
#			if station > 0:
#				station -= 1
#			else:
#				station = maxstation
#		return(station)

	def load2(self):
		''' This is the current loader. '''
		lines = []
		maxstation = self.stationcount()
		self.logger.info("Getting BBC stations loaded")		# refresh periodically
		try:
			subprocess.Popen("rm -f *.pls", shell=True)			# need the -f to force removal of unwritable files
			q = subprocess.Popen('mpc -q clear', shell=True)
			q.wait()
		except:
			self.logger.warning("Failed to clear old pls files.")
			return(maxstation)
		for i in self.urls:
			self.logger.info("Fetching: "+i[self.URLID])
			try:
				p = subprocess.Popen('wget -q http://www.bbc.co.uk/radio/listen/live/'+i[self.URLSTREAM], shell=True)	# need to trap errors here.
				p.wait()		# need to wait for the last cmd to finish before we can read the file.
			except HTTPError, e:
				self.logger.error("Failed to fetch address for "+i[self.URLID])
				maxstation -= 1					# not as many as we planned
		for i in self.urls:
			self.logger.info("Opening the stream file: "+i[self.URLSTREAM])
#			time.sleep(.5)					# seem to need this for the file to be ready for next line.
			try:
				source=open(i[self.URLSTREAM],'r')
				source.readline()				# this dumps first line of file
				source.readline()
				lines.append(source.readline())
				source.close()					# do we need this??
			except:
				logging.warning("Could not open: "+i[self.URLSTREAM])
		for line in lines:
			try:
				q = subprocess.Popen("mpc -q add "+re.escape(line[6:]), shell=True)	# use the re.escape to escape the & which was breaking up the string
			except:
				self.logger.warning("Failed to add file to playlist")
			q.wait()
		return(maxstation)
		
	def stationscanner(self):
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
	myBBC.stationscanner()