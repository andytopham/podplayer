#!/usr/bin/python
'''Podcast + internet radio player.'''
import os
import sys			# required for sys.exit()
import time, datetime, argparse, logging
# from gpio import Gpio
import executive

LOGFILE = 'log/radio.log'
VERSION = '6.1'

''' 
Class structure (ignoring library calls)
radio ->executive	-> gpio 	-> infodisplay	-> tft or oled
					-> mpc
					-> system
					-> timeout
'''

def _setup_sockets():
	'''For client/server operation. Not being used yet.'''
	# Enable server and remote client
	MySocket = comms.Comms()
	if config.master == True:
		print "I am a server"
		slave = MySocket.registerserversetup()
		if slave != 0:
			time.sleep(1)
			# send the initial handshake message
			MySocket.send2cmd(slave,"Msg from master.")
			# ready to send commands, but setup the link first...
			MySocket.setupsender(slave)
	else:
		print "I am a client"
		slave = 0
		MySocket.registerclient(config.remote)
		# now we are registered, just fetch the initial handshake message.
		MySocket.setuplistener()
		# now listen for real commands
	#	time.sleep(2)
		MySocket.cmdlistener()
			
def _radio_start(v=0):
	'''	The main routine for iRadio.'''
	print "podplayer v", VERSION
	logging.info('******************')
	logging.warning("podplayer v"+VERSION)
	myExecutive = executive.Executive()
	myExecutive.startup(v)
	logging.info("Starting main podplayer loop")
	myExecutive.master_loop()
			
if __name__ == "__main__":
	'''	iradio main routine. Set up logging before calling radiostart.'''
	parser = argparse.ArgumentParser(
			description='podplayer - the radio and podcast appliance.')
	parser.add_argument("-v", "--verbose", 
			help="increase output to log",
			action="store_true")
	args = parser.parse_args()
	if args.verbose:
		verbose = 1
		logging.basicConfig(	filename=LOGFILE,
								filemode='w',
								level=logging.DEBUG )
	else:
		verbose = 0
		logging.basicConfig(	filename=LOGFILE,
								filemode='w',
								level=logging.WARNING )
	
#	Default level is warning, level=logging.INFO log lots, 
#		level=logging.DEBUG log everything
	logging.warning('*********************************')
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')
			+". Running radio class as a standalone app")
	if verbose == 0:
		logging.warning("Use -v command line option to increase logging.")
	else:
		logging.warning("Logging = verbose.")
	
	#Constants
	logging.info("Running radio class as a standalone app")
	_radio_start(verbose)
	
	