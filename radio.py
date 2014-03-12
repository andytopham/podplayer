#!/usr/bin/python
'''Podcast + internet radio player.'''
import os
import sys			# required for sys.exit()
import time
import datetime
import argparse
import logging
import oled			# my second module.
import gpio			# my third module.
import mpc2 as mpc			# my fourth module.
import weather		# my fifth module.
import timeout		# my timeout module
import comms		# the remote control stuff.
import system		# my disk usage
import config		# the hardware and constants file

LOGFILE = '/home/pi/podplayer/log/radio.log'

def _setup_sockets():
	# Enable server and remote client
	mySocket = comms.comms()
	if config.master == True:
		print "I am a server"
		slave = mySocket.registerserversetup()
		if slave != 0:
			time.sleep(1)
			# send the initial handshake message
			mySocket.send2cmd(slave,"Msg from master.")
			# ready to send commands, but setup the link first...
			mySocket.setupsender(slave)
	else:
		print "I am a client"
		slave = 0
		mySocket.registerclient(config.remote)
		# now we are registered, just fetch the initial handshake message.
		mySocket.setuplistener()
		# now listen for real commands
	#	time.sleep(2)
		listenconnection = mySocket.cmdlistener()
			
def _radio_start(verbose):
	'''	The main routine for iRadio.'''
	print "podplayer v",config.version
	logging.info('******************')
	logging.warning("podplayer v"+str(config.version))
	logging.info("Setting time")
	os.environ['TZ'] = 'Europe/London'
	time.tzset
	myGpio=gpio.gpio()
	myOled = oled.oled()
	myMpc = mpc.Mpc()
	mySystem = system.System()
	mySystem.disk_usage()
	myTimeout = timeout.timeout(verbose)
	station = 0
	NEWTIMEOUTSTRING= 'STOP '
	TIMEOUTSTRING = '               .  '
	programmename = ""
	
	myOled.writerow(1,"podplayer v"+config.version+"      ")
	myWeather=weather.weather()
	temperature = myWeather.wunder(config.key,config.locn)

	myMpc.play()
	programmename = myMpc.progname()
	myOled.writerow(1,str(programmename))
	myOled.updateoled(temperature, station)

	logging.info("Starting main podplayer loop")
	
	while True:
		# regular events first
		time.sleep(.2)
		myOled.scroll(programmename)
		
		# process the timeouts
		t = myTimeout.checktimeouts()
		if t == config.UPDATEOLED:
			programmename = myMpc.progname()
			myOled.updateoled(temperature, station)		# this has to be here to update time
		if t == config.UPDATETEMPERATURE:
			temperature = myWeather.wunder(config.key,config.locn)
			myOled.updateoled(temperature, station)
		if t == config.UPDATESTATION:
			myMpc.loadbbc()						# handles the bbc links going stale
			if mySystem.disk_usage():
				programmename = "Out of disk."
				myOled.writerow(1,programmename)
				sys.exit()
		if t == config.AUDIOTIMEOUT:
			programmename = TIMEOUTSTRING
			myMpc.audioTimeout()
			myOled.writerow(1,programmename)
		
		# now process the button presses
		button = myGpio.processbuttons()
		if button != 0:
			myTimeout.resetAudioTimeout()
		if button == config.BUTTONMODE:
			myOled.writerow(1,"<<Mode change>> ")
			station = myMpc.switchmode()
			programmename = myMpc.progname()
			myOled.writerow(1,programmename)
			start = datetime.datetime.now()
			audiostart = datetime.datetime.now()
#			myMpc.cleanoldpods()

		elif button == config.BUTTONNEXT:
			myOled.writerow(1,"<<Next>>        ")
			station = myMpc.next()
			if station == -1:
				programmename = "No pods left!"
			else:
				programmename = myMpc.progname()
			myOled.writerow(1,programmename)
			start = datetime.datetime.now()
			audiostart = datetime.datetime.now()
#			myMpc.cleanoldpods()

		elif button == config.BUTTONSTOP:
			if myMpc.playState == 1:
				myOled.writerow(1,"<<Stopping>>      ")
				myMpc.toggle()
				programmename = myMpc.progname()
			else:
				myOled.writerow(1,"<<Starting>>      ")
				myMpc.toggle()
				programmename = myMpc.progname()
			audiostart = datetime.datetime.now()

		elif button == config.BUTTONVOLUP:
			myMpc.chgvol(+1)
			audiostart = datetime.datetime.now()

		elif button == config.BUTTONVOLDOWN:
			myMpc.chgvol(-1)
			audiostart = datetime.datetime.now()
			
if __name__ == "__main__":
	'''	iradio main routine. Sets up the logging and constants, before calling radiostart.'''
	parser = argparse.ArgumentParser( description='podplayer - the BBC radio and podcast appliance. \
	Use -v option when debugging.' )
	parser.add_argument("-v", "--verbose", help="increase output - lots more logged in ./log/radio.log",
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
	
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning('*************************************')		# divider from last run
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running radio class as a standalone app")
	logging.warning("Use -v command line option to increase logging.")

	#Constants
	logging.info("Running radio class as a standalone app")
	_radio_start(verbose)
	
	