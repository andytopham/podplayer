#!/usr/bin/python
# tft.py
# My routines for writing to the 2.2" TFT.
# This calls on info from Adafruit at:
# https://github.com/adafruit/Adafruit_Python_ILI9341
# Fonts come from dafont.com, and are stored in a 'binary' subdirectory.
# Need to send to rpi using binary transfer.

import Image
import ImageDraw
import ImageFont

import time
import Adafruit_ILI9341 as TFT
#import Adafruit_GPIO.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO

# Setup which pins we are using to control the oled
RST = 23
DC    = 18
SPI_PORT = 0
SPI_DEVICE = 0
# Using a 5x8 font
FONT_DIR = '/home/pi/fonts/'
ROW_HEIGHT = 8
ROW_LENGTH = 20
NO_OF_ROWS = 12
ROW_LENGTH = 17
BIG_ROW = 1
# gpio pin definitions
L_BUTTON = 19
R_BUTTON = 4
WHITE = (255,255,255)
RED = (255,0,0)
YELLOW = (255,255,0)
BLACK = (0,0,0)
BLUE = (0,0,255)

class Screen:
	def __init__(self, rowcount = NO_OF_ROWS, rotation = 0):
		self.rotation = rotation
		self.disp = TFT.ILI9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))
		self.disp.begin()
		self.disp.clear()	# black
		self.old_text = [' ' for i in range(NO_OF_ROWS)]	# used for clearing oled text
#		self.font = ImageFont.load_default()
#		self.font = ImageFont.truetype('binary/morningtype.ttf',FONTSIZE)
#		self.font = ImageFont.truetype('binary/secrcode.ttf',FONTSIZE)
#		self.font = ImageFont.truetype('binary/DS-DIGI.TTF',FONTSIZE)
		self.font = [ImageFont.load_default() for i in range(NO_OF_ROWS)]
		self.fontsize = [24 for i in range(NO_OF_ROWS)]
#		self.fontsize[BIG_ROW] = 36
		for i in range(NO_OF_ROWS):
			self.font[i] = ImageFont.truetype(FONT_DIR+'Hack-Regular.ttf',self.fontsize[i])
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(L_BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_UP)
		GPIO.setup(R_BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_UP)

	def info(self):
		return(NO_OF_ROWS, ROW_LENGTH)
		
	def writelabels(self, next = False, stop = False):
		if next:
			self.writerow(self.rowcount-1, '****         Stop')
#			time.sleep(.5)
		if stop:
			self.writerow(self.rowcount-1, 'Next         ****')
#			time.sleep(.5)
		else:
			self.writerow(self.rowcount-1, 'Next         Stop')
		return(0)
		
	def write_radio_extras(self, clock, temperature):
		self.writerow(self.rowcount-2,'{0:5s}   {1:7.1f}^C'.format(clock,float(temperature)))		
		return(0)
		
	def _draw_rotated_text(self, image, text, position, angle, font, fill=WHITE):
		# Get rendered font width and height.
		draw = ImageDraw.Draw(image)
		width, height = draw.textsize(text, font=font)
		# Create a new image with transparent background to store the text.
		textimage = Image.new('RGBA', (width, height), (0,0,0,0))
		# Render the text.
		textdraw = ImageDraw.Draw(textimage)
		textdraw.text((0,0), text, font=font, fill=fill)
		# Rotate the text image.
		rotated = textimage.rotate(angle, expand=1)
		# Paste the text into the image, using it as a mask for transparency.
		image.paste(rotated, position, rotated)

	def scroll_text(self,rownumber,text):
		''' So far just scrolls one row.'''
#		print 'Scrolling row number ',rownumber
		x = 0
		y = ROW_HEIGHT * rownumber-1
		i = 0
		time.sleep(1)
		while i < len(text)-ROW_LENGTH:
			todraw = '{: <20}'.format(text[i:])
			self.MySsd.draw_text2(x,y,todraw,1)
			self.MySsd.display()
			i += 1
		time.sleep(1)
		return(0)
	
	def writerow(self, rownumber, string, clear=True):
		'''Now runs from row 0.'''
		if rownumber == 0:
			fill_colour = YELLOW
		elif rownumber == NO_OF_ROWS-1:
			fill_colour = BLUE
		else:
			fill_colour = WHITE
		if rownumber == 12:
			fontsize = 60
		else:
			fontsize = 24		
		if self.rotation == 0:
			xpos = 0
			ypos = 0
			for i in range (rownumber):
				ypos += self.fontsize[i-1]
#			ypos = rownumber * fontsize				
		else:
			ypos = 0
			xpos = 0
			for i in range (rownumber):
				xpos += self.fontsize[i-1]
		thisfont = self.font[rownumber]
		if clear == True:
			self._draw_rotated_text(self.disp.buffer, self.old_text[rownumber], (xpos, ypos), self.rotation, thisfont, fill=BLACK)
		self._draw_rotated_text(self.disp.buffer, string, (xpos, ypos), self.rotation, thisfont, fill=fill_colour)
		self.old_text[rownumber] = string
		self.display()
		return(0)
		
	def draw_blob(self,x,y):
		self.MySsd.draw_pixel(x,y,True)
#		self.MySsd.draw_pixel(x+1,y,True)
#		self.MySsd.draw_pixel(x,y+1,True)
#		self.MySsd.draw_pixel(x+1,y+1,True)
		return(0)
		
	def delete_blob(self,x,y):
		self.MySsd.draw_pixel(x,y,False)
#		self.MySsd.draw_pixel(x+1,y,True)
#		self.MySsd.draw_pixel(x,y+1,True)
#		self.MySsd.draw_pixel(x+1,y+1,True)
		return(0)
		
	def write_counter(self):
		x = 0
		for x in range(100):
			self.writerow(5, str(x), True)
			self.display()
			time.sleep(1)
			
	def show_time(self):
		while True:
			date_now = '{:<18}'.format(time.strftime("%b %d %Y ", time.gmtime()))
			time_now = '{:<8}'.format(time.strftime("%H:%M:%S", time.gmtime()))
			self.writerow(0, 'TFT self test running...', True)	
			self.writerow(1, time_now+' ', True)	
			self.writerow(2, date_now, True)	
			for i in range(3,NO_OF_ROWS-2):
				self.writerow(i, 'Row '+str(i), True)	
			self.display()
			time.sleep(0.5)
			if GPIO.input(L_BUTTON):
#				print 'Left button',
				self.writerow(NO_OF_ROWS-2, 'Left button true', True)
			else:
#				print 'no L button',
				self.writerow(NO_OF_ROWS-2, 'Left button false', True)
			if GPIO.input(R_BUTTON):
#				print 'Right button'
				self.writerow(NO_OF_ROWS-1, 'Right button true', True)
			else:
#				print 'no R button'
				self.writerow(NO_OF_ROWS-1, 'Right button false', True)
			self.display()
		return(0)
	
	def display(self):
		self.disp.display()
		return(0)

if __name__ == "__main__":
	print 'TFT test'		
	MyScreen = Screen()
	MyScreen.show_time()
	