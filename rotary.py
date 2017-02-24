#!/usr/bin/python
# Rotary encoder code
#  from: https://www.raspberrypi.org/forums/viewtopic.php?f=37&t=140250

import RPi.GPIO as GPIO
import threading
from time import sleep
# import Adafruit_CharLCD as LCD
import lcd

Enc_A = 4              # Encoder input A: input GPIO 4 
Enc_B = 17             # Encoder input B: input GPIO 14 
Sw = 18

class Rotary():
	def __init__(self):
		self.Rotary_counter = 0           # Start counting from 0
		self.Current_A = 1               # Assume that rotary switch is not 
		self.Current_B = 1               # moving while we init software
		self.LockRotary = threading.Lock()      # create lock for rotary switch
		GPIO.setwarnings(True)
		GPIO.setmode(GPIO.BCM)               # Use BCM mode
		GPIO.setup(Enc_A, GPIO.IN, GPIO.PUD_UP)             
		GPIO.setup(Enc_B, GPIO.IN, GPIO.PUD_UP)
		GPIO.setup(Sw, GPIO.IN, GPIO.PUD_UP)
		GPIO.add_event_detect(Enc_A, GPIO.RISING, callback=self.rotary_interrupt)             # NO bouncetime 
		GPIO.add_event_detect(Enc_B, GPIO.RISING, callback=self.rotary_interrupt)             # NO bouncetime 
		GPIO.add_event_detect(Sw, GPIO.FALLING, callback=self.switch_interrupt)             # NO bouncetime
		return

	def switch_interrupt(self, junk):
		print "Switch"
		return
		
	def rotary_interrupt(self, A_or_B):
		Switch_A = GPIO.input(Enc_A)
		Switch_B = GPIO.input(Enc_B)
		if self.Current_A == Switch_A and self.Current_B == Switch_B:      # Same interrupt as before (Bouncing)?
			return                              # ignore interrupt!
		self.Current_A = Switch_A                        # remember new state
		self.Current_B = Switch_B                        # for next bouncing check
		if (Switch_A and Switch_B):                  # Both one active? Yes -> end of sequence
			self.LockRotary.acquire()                  # get lock 
			if A_or_B == Enc_B:                     # Turning direction depends on 
				self.Rotary_counter += 1                  # which input gave last interrupt
			else:                              # so depending on direction either
				self.Rotary_counter -= 1                  # increase or decrease counter
			self.LockRotary.release()
		return

if __name__ == "__main__":
	print "Running rotary class as a standalone app"
	Volume = 0                           # Current Volume   
	NewCounter = 0                        # for faster reading with locks
	myRotary = Rotary()
	myRotary.init()                              # Init interrupts, GPIO, ...
#	lcd = LCD.Adafruit_CharLCD(27, 22, 25, 24, 23, 5, 16, 2, 21) 
	myLcd = lcd.Screen()
	myLcd.writerow(0, 'LCD initialised')
	while True :                        # start test 
		sleep(0.1)                        # sleep 100 msec
		myRotary.LockRotary.acquire()               # get lock for rotary switch
		NewCounter = myRotary.Rotary_counter         # get counter value
		myRotary.Rotary_counter = 0                  # RESET IT TO 0
		myRotary.LockRotary.release()               # and release lock
		if (NewCounter !=0):               # Counter has CHANGED
			Volume = Volume + NewCounter*abs(NewCounter)   # Decrease or increase volume 
			if Volume < 0:                  # limit volume to 0...100
				Volume = 0
			if Volume > 100:               # limit volume to 0...100
				Volume = 100
			print NewCounter, Volume         # some test print
			myLcd.writerow(1, str(Volume)+' ')
