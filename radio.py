#!/usr/bin/python
'''Podcast + internet radio player.'''
import os
import sys			# required for sys.exit()
import time, datetime
import argparse, logging
import oled, gpio, timeout, comms, system, config		# my modules.
import mpc2 as mpc			# my updated module.

LOGFILE = '/home/pi/podplayer/log/radio.log'

def _setup_sockets():
	'''For client/server operation. Not being used yet.'''
	# Enable server and remote client
	MySocket = comms.comms()
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

def _process_timeouts(myOled, myMpc, mySystem, t):
	'''Cases for each of the timeout types.'''
	if t == config.UPDATEOLED:
		myOled.update_row2(0)		# this has to be here to update time
	if t == config.UPDATETEMPERATURE:
		myOled.update_row2(1)
	if t == config.UPDATESTATION:
		myMpc.loadbbc()						# handles the bbc links going stale
		if mySystem.disk_usage():
			myOled.writerow(1, 'Out of disk.')
			sys.exit()
		else:
			return('Reloaded stations')
	if t == config.AUDIOTIMEOUT:
		myMpc.audioTimeout()
		return('Timeout')
	return(myMpc.progname())

def _process_button_presses(myMpc, button):
	'''Cases for each of the button presses and return the new prog name.'''
	if button == config.BUTTONMODE:
		myMpc.switchmode()
	elif button == config.BUTTONNEXT:
		if myMpc.next() == -1:
			return('No pods left!')
	elif button == config.BUTTONSTOP:
		myMpc.toggle()
	elif button == config.BUTTONVOLUP:
		myMpc.chgvol(+1)
	elif button == config.BUTTONVOLDOWN:
		myMpc.chgvol(-1)
	return(myMpc.progname())
			
def _radio_start(v=0):
	'''	The main routine for iRadio.'''
	print "podplayer v", config.version
	logging.info('******************')
	logging.warning("podplayer v"+str(config.version))
	myGpio=gpio.gpio()
	myOled = oled.Oled()
	myMpc = mpc.Mpc()
	mySystem = system.System()
	myTimeout = timeout.Timeout(v)
	myOled.writerow(1, "podplayer v"+config.version+"      ")
	programmename = myMpc.progname()
	myOled.writerow(1, programmename)
	logging.info("Starting main podplayer loop")
	
	while True:
		# regular events first
		time.sleep(.2)
		myOled.scroll(programmename)
		timeout_type = myTimeout.checktimeouts()
		if timeout_type != 0:
			programmename = _process_timeouts(myOled, myMpc, mySystem, timeout_type)
		button = myGpio.processbuttons()
		if button != 0:
			myTimeout.resetAudioTimeout()
			programmename = _process_button_presses(myMpc, button)
			
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
	logging.warning("Use -v command line option to increase logging.")

	#Constants
	logging.info("Running radio class as a standalone app")
	_radio_start(verbose)
	
	