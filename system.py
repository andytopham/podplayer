#!/usr/bin/python
'''Check OS stability.'''
import time
import datetime
import argparse
import logging
import subprocess
import config		# the hardware and constants file

LOGFILE = '/home/pi/podplayer/log/'

class System:
	'''Return state of OS stability'''
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		
	def disk_usage(self):
#		p = subprocess.check_output(['sudo', 'du', '-h', '-d', '1'])
		p = subprocess.check_output(['df', '-l'])
		line = p.splitlines()[1]
		percent = line.split()[4]
		print 'Disk space used: '+percent
		self.logger.warning('Disk space used: '+percent)
		if int(percent.rstrip('%')) > 50:
			self.logger.warning('Running out of disk space. Used: '+percent)
			self.logger.warning('Find disk space usage by: sudo du -h -d 1')
			return(0)
		if int(percent.rstrip('%')) > 80:
			self.logger.warning('Seriously running out of disk space. Used: '+percent)
			self.logger.warning('Find disk space usage by: sudo du -h -d 1')
			return(1)		
		return(0)

if __name__ == "__main__":
	'''Print disk usage.'''
#	print "Running system class as a standalone app"
	print __doc__
	logging.basicConfig(filename=LOGFILE+'system.log',
						filemode='w',
						level=logging.INFO)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running system class as a standalone app")

	mySystem = system()
	mySystem.disk_usage()
	