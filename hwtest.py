#!/usr/bin/python
# hwtest.py
# A test of the button and display hardware.

import oled, gpio
import time

myScreen = oled.Screen(4)
myGpio = gpio.Gpio()
#myGpio.setup()

myScreen.writerow(0,'HW test')
myScreen.writerow(2,'Nx St V- V+ ')

print myGpio.pins
while True:
	string = ''
	states = myGpio.read()
	print states
	for i in range(len(states)):
		string += str(states[i])+'  '
	myScreen.writerow(1,string)
	time.sleep(.5)

	