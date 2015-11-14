''' uoled.py
	Completely replaces oled.py.
	Called by infodisplay.py
'''
import gaugette.ssd1306
import time
import sys
from time import gmtime, strftime

# Setting some variables for our reset pin etc.
# This numbering comes from wiringpi.
#RESET_PIN = 5		# gpio24	pin18
#DC_PIN    = 4		# gpio23	pin16
#RESET_PIN = 6		# gpio25	pin22
RESET_PIN = 15
DC_PIN    = 16
#DC_PIN    = 0		# gpio17	pin11	

class Oled():
	def __init__(self, rowcount):
		self.led = gaugette.ssd1306.SSD1306(reset_pin=RESET_PIN, dc_pin=DC_PIN)
		self.led.begin()
		self.led.clear_display() # This clears the display but only when there is a led.display() as well!
		time.sleep(1)
		self.led.display()
		time.sleep(1)
		self.led.draw_text2(0,0,'Init uoled',1)
		self.led.display()
		time.sleep(1)

	def writerow(self, row, string):
		if row == 1:
			x = 0
			y = 0
		if row == 2:
			x = 0
			y = 8
		if row == 3:
			x = 0
			y = 16
		if row == 4:
			x = 0
			y = 24
		self.led.draw_text2(x,y,string,1)
		self.led.display()
		return(0)
		
