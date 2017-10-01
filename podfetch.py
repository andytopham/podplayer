#!/usr/bin/python
""" Pulls podcasts from the web and puts them in the destin dir.
	Failing podcasts:
	Amp Hour.
	Wired.
"""
import feedparser
import time
import subprocess
import urllib
import logging
import datetime
import wget

LOGFILE = './log/podfetch.log'

class podfetch:
	''' A class to fetch podcasts from the web and leave them ready for playing by mpd. '''
	
	def __init__(self):
		''' Setup the list of podcast feeds. '''
		self.podlist = [['TOTD','http://downloads.bbc.co.uk/podcasts/radio4/totd/rss.xml'],
					['MoreOrLess','http://downloads.bbc.co.uk/podcasts/radio4/moreorless/rss.xml'],
					['TWIT','http://feeds.twit.tv/twit'],
					['TWIG','http://leo.am/podcasts/twig'],
					['99PercentInvisible','http://feeds.99percentinvisible.org/99percentinvisible']
					]

		self.destinationdir = "/var/lib/mpd/music"
		
	def podwget(self, urltuple):
		''' Open the feed list and then fetch the top items from that feed. '''
		label,url = urltuple
		print "Fetching list: ",label
		d = feedparser.parse(url)
		for j,i in enumerate(d.entries):
			if j == 0:			# so far only get the first item from the feed.
				print i.link
				string = label + ": " + i.title
				print string
				logging.info(string)
				# replace this next line with the native python wget???
#				p = wget.download(i.link)	# need to set destin dir with -o option.
#				p = subprocess.call(["wget", "-q", "-nc", "-P", self.destinationdir, i.link])
				p = subprocess.call(["wget", "-q", "-P", self.destinationdir, i.link])
		return(0)

	def podrssprocess(self):
		''' Open each rss url and call the routine to fetch the pods from each one. '''
		print ">>> podcatcher <<<"
		for k in self.podlist:
			self.podwget(k)
		print
		print "List of files available to mpd: "
		logging.info("List of files available to mpd: ")
		p = subprocess.check_output(["ls", self.destinationdir])
		for i in p.splitlines():
			print i
			logging.info(str(i))
		print "Starting db initialise..."
		p = subprocess.check_output(["mpc", "update"])	# reinitialise the db

if __name__ == "__main__":
	''' Typically run this as a standalone prog to collect the podcasts asynchronously from the playing. '''
	logging.basicConfig(	filename = LOGFILE,
							filemode='w',
							level=logging.INFO )
	
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running podfetch class as a standalone app")

	myPodfetch = podfetch()
	myPodfetch.podrssprocess()
	
