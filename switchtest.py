#!/usr/bin/python
'''Test switch hardware with output to local oled.'''
import os
import sys			# required for sys.exit()
import time, datetime, argparse, logging
import RPi.GPIO as GPIO
from gpio import Gpio
from oled import Oled

myGpio=Gpio()
myOled=Oled(4)

myGpio.setup()
myOled.writerow(1,'Switch test')

a = [17,18,21,22,23,24,25,4]
b = [0,0,0,0,0,0,0,0]
for i in range(len(a)):
	GPIO.setup(a[i],GPIO.IN)
	print a[i]," ",
print
print 'Next Stop Vol+ Vol- -    -    -    -'
time.sleep(1)
myOled.writerow(1,str(a[0])+' '+str(a[1])+' '+str(a[2])+' '+str(a[3])+' '+str(a[4])+' '+str(a[5]))
myOled.writerow(3,str(a[6])+' '+str(a[7]))

while True:
	for i in range(len(a)):
		print GPIO.input(a[i]),"  ",	
		b[i] = GPIO.input(a[i])	
	print
	myOled.writerow(2,str(b[0])+'  '+str(b[1])+'  '+str(b[2])+'  '+str(b[3])+'  '+str(b[4])+'  '+str(b[5]))
	myOled.writerow(4,str(b[6])+'  '+str(b[7]))
	time.sleep(.5)
		
