#!/usr/bin/python
''' 
  iRadio - internet radio.
  This is the config file for iRadio.
  Sets up the various different configurations for the varying hardware.
  And stores the keys.
  
'''
version = "3.8"
master = True
remote = "192.168.0.135"		# api1 as server
#Constants
FULL = 1
PARTIAL = 0
# Button polarity
#PRESSED = True
PRESSED = False
# Used to pass the button push status
BUTTONNONE = 0
BUTTONNEXT = 1
BUTTONSTOP = 2
BUTTONVOLUP = 3
BUTTONVOLDOWN = 4
BUTTONMODE = 5
BUTTONREBOOT = 6
UPDATEOLED = 1
UPDATETEMPERATURE = 2
UPDATESTATION = 3
AUDIOTIMEOUT = 4

device = FULL		# now overwritten by hw scanning

audiotimeout = 30		# minutes
# These next rows need completing manually locally
key = ''
locn = ''
bbckey = ''
# oled config
rowlength = 20
rowcount = 4