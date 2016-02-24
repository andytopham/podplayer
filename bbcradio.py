#!/usr/bin/python
''' Load BBC radio stations into mpd.'''
import re, subprocess, time, logging, datetime, requests
from bs4 import BeautifulSoup
import mpd
import threading

STATIONNAMERESETTIME = 2*60

class BBCradio(threading.Thread):
	# These are the indicies to the url array.
	URLID = 0
	URLSTREAM = 1
	URLDETAILS = 2
	NAME = 3
	urls = [["BBCR2",	"r2_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_two" ],
			["BBCR4",	"r4_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_four" ],
			["BBCR4x",	"r4x_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_four_extra"],
#			["BBCR5",	"r5l_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_five_live"],
			["BBCR6",	"r6_aaclca.pls",	"http://www.bbc.co.uk/radio/player/bbc_6music"]
			]
	newurls = [["BBCR2",	"bbcradio2.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_two" ],
			["BBCR4",		"bbcradio4fm.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_four" ],
			["BBCR4x",		"bbcradio4extra.pls",	"http://www.bbc.co.uk/radio/player/bbc_radio_four_extra"],
#			["BBCR5",		"bbc5live.pls",		"http://www.bbc.co.uk/radio/player/bbc_radio_five_live"],
			["BBCR6",		"bbc6music.pls",	"http://www.bbc.co.uk/radio/player/bbc_6music"]
			]		
	def __init__(self, mpd_channel):
		self.Event = threading.Event()
		threading.Thread.__init__(self, name='mybbc')
		self.mpd_channel = mpd_channel
		self.logger = logging.getLogger(__name__)
		self.expiry_times = [None]*6
		self.stationcount = 0
		self.bbcname = ['Not yet available']*5
#		self.t = threading.Timer(STATIONNAMERESETTIME, self.stationname)
#		self.t.start()
#		self.t.name = 'bbcstnname'

	def run(self):
		print 'Starting bbc collection.'
		myevent = False
		while not myevent:
			if self.load(self.mpd_channel) != 0:
				print 'BBC load error.'
				self.logger.error('BBC load error')
				myevent = True
			time.sleep(2)			# temporary
			myevent = self.Event.wait(60*60)		# wait for this timeout or the flag being set.
		print 'BBC exiting.'

	def cleanup(self):
		self.t.cancel()
		time.sleep(1)
		self.Event.set()			# send the stop signal
		time.sleep(1)

	def stationcounter(self):
		'''Return the number of radio station urls.'''
		self.logger.info("Counting stations. Count="+str(len(self.urls)))
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
	
	def _new_refresh_pls_files(self):
		'''Works with the Feb 2015 BBC format.'''
		try:
			subprocess.Popen("rm -f *.pls", shell=True)		# need the -f to force removal of unwritable files
			q = subprocess.Popen('mpc -q clear', shell=True)
			q.wait()
		except:
			self.logger.error('Failed to clear old pls files.', exc_info=True)
			return(1)
		for i in self.newurls:
			self.logger.info("Fetching: "+i[self.URLID])
			try:
				p = subprocess.Popen('wget -q http://www.radiofeeds.co.uk/'
									+i[self.URLSTREAM], shell=True)
				p.wait()		# wait for last cmd to finish before we can read the file.
			except HTTPError, e:
				self.logger.error("Failed to fetch address for "+i[self.URLID], exc_info=True)
				return(1)
		return(0)
	
	def oldload(self, mpd_channel):
		'''Load the stations stored in the urls array. '''
		try:
			mpd_channel.connect("localhost", 6600)		# refresh the connection
		except:
			pass		# it must be already connected
		lines = []
		self.logger.warning("Getting BBC stations loaded")
		if self._refresh_pls_files():
			return(1)
		self.stationcount = 0
		for i in self.urls:
			self.logger.info("Opening the stream file: "+i[self.URLSTREAM])
			try:
				source=open(i[self.URLSTREAM],'r')
				self.stationcount += 1
				header = source.readline()				# this dumps first line of file
				if header != '[playlist]\n':
					print 'Invalid pls file contents:',t
					return(1)
				source.readline()		# NumberOfEntries=2
				file1 = source.readline()
				source.readline()		# Title1=No Title
				source.readline()		# Length1=-1
				file2 = source.readline()
				lines.append(file1)		# or, we could choose file1 - don't know difference
				source.close()
#				print lines				
			except:
				logging.warning("Could not open: "+i[self.URLSTREAM])
				return(-1)
		for index, line in enumerate(lines):
			try:
				self.logger.info("Loading: "+line[6:])
				self._get_end_time(index, line[6:])
				mpd_channel.addid(line[6:].rstrip('\n'))
			except:
				self.logger.warning("Failed to add file to playlist: "+line[6:])
				return(-1)
		self.logger.info('Loaded BBC stations.')
		print 'Loaded BBC stations.'
		return(0)
		
	def load(self, mpd_channel):
		'''Load the stations stored in the urls array. Feb 2015 edition. '''
		try:
			mpd_channel.connect("localhost", 6600)		# refresh the connection
		except:
			pass		# it must be already connected
		lines = []
		self.logger.warning("Getting BBC stations loaded")
		if self._new_refresh_pls_files():
			return(1)
		self.stationcount = 0
		for i in self.newurls:
			self.logger.info("Opening the stream file: "+i[self.URLSTREAM])
			try:
				source=open(i[self.URLSTREAM],'r')
				self.stationcount += 1
				header = source.readline()				# this dumps first line of file
				file1 = source.readline()
				title = source.readline()		# Title1=No Title
				lines.append(file1)		# or, we could choose file1 - don't know difference
				source.close()
			except:
				logging.warning("Could not open: "+i[self.URLSTREAM])
				return(-1)
		for index, line in enumerate(lines):
			try:
				self.logger.info("Loading: "+line[6:])
				self._get_end_time(index, line[6:])
				mpd_channel.addid(line[6:].rstrip('\n').rstrip('\r')) # extra \r to remove with new format
			except:
				self.logger.warning("Failed to add file to playlist: "+line[6:])
				return(-1)
		self.logger.info('Loaded BBC stations.')
		print 'Loaded BBC stations:', self.stationcount
		return(0)
		
	def _get_end_time(self,i, link):
		'''Extract the end time from the link.'''
		now = time.time()
		e = link.split('&e=')[1]
		end = float(e.split('&h=')[0])
		mins_left = int((end - now)/60)
		self.logger.info('Time left:'+str(mins_left))
		self.expiry_times[i] = end
		return(0)
		
	def check_time_left(self, station):
		'''Return the time left before we get to the end time for this stream'''
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

	def stationname(self):
		"""Fetch the names of all the BBC programmes."""
		self.logger.info("Stationname: Fetching BBC radio program names.")
#		print 'Fetching BBC names'
		for station in range(4):
			row = self.urls[station]
			address = row[self.URLDETAILS]
			try:
				soup = BeautifulSoup(requests.get(address).text,"html.parser")
			except requests.ConnectionError:
				self.logger.error("Connection error getting prog info")
				self.bbcname[station] = "Connection error "
			else:
				try:
					programmename = unicode(soup.title.string)
				except:
					programmename = "Unpronounceable"
			self.logger.info("Program name:"+programmename)
#			print programmename
			self.bbcname[station] = programmename
		# restart the timer
		self.t = threading.Timer(STATIONNAMERESETTIME, self.stationname)
		self.t.start()
		self.t.name = 'bbcstnname'

				
if __name__ == "__main__":
	print "Running bbcradio class as a standalone app"
	logging.basicConfig(filename='log/bbcradio.log',
						filemode='w',
						level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running bbcradio class as a standalone app")

	myBBC = BBCradio()
	
	client = mpd.MPDClient()
	client.timeout = 10 # seconds
	client.idletimeout = None
	client.connect("localhost", 6600)
	client.clear()
#	self.logger.info("python-mpd2 version:"+client.mpd_version)
	myBBC.load(client)
#	myBBC._stationscanner()