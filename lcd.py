#!/usr/bin/python
# LCD control.
# Use with Hobbytronics LCD16X2WB
# This code calls the Adafruit LCD library as described in...
# https://learn.adafruit.com/character-lcd-with-raspberry-pi-or-beaglebone-black/overview

import Adafruit_CharLCD as LCD

class Screen:
	def __init__(self, rows = 2):
		self.lcd = LCD.Adafruit_CharLCD(27, 22, 25, 24, 23, 5, 16, 2, 21)   
		self.lcd.message('LCD initialised')
		self.rowcount = rows
		if rows == 2:
			self.rowlength = 16
		else:
			self.rowlength = 20

	def info(self):
		return(self.rowcount, self.rowlength)

	def write_button_labels(self, next, stop):
		# These are the botton labels. No labels with small display.
		if next == True:
			self.writerow(1,'Next')
		if stop == True:
			self.writerow(1,'Stop')
		return(0)
		
	def write_radio_extras(self, string1, temperature, chgvol_flag = False):
		if chgvol_flag:
			self.q.put([self.rowcount-1, string1])
		else:
			self.q.put([self.rowcount-1,'{0:5s}{1:7.1f}^C'.format(string1.ljust(self.rowlength-9),float(temperature))])		
		return(0)
		
	def clear(self):
		self.lcd.clear()
		return

	def writerow(self,row,string):
		if row < self.rowcount:
			self.lcd.set_cursor(0,row)
			self.lcd.message(string)
		return
	
	def scroll(self,string):
		return
		
if __name__ == "__main__":
	print "Running lcd class as a standalone app"
	myLcd = Screen()
	
