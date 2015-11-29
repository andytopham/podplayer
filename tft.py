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
#import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

# Setup which pins we are using to control the oled
RST = 23
DC    = 18
SPI_PORT = 0
SPI_DEVICE = 0
# Using a 5x8 font
ROW_HEIGHT = 8
ROW_LENGTH = 20

class Screen:
	''' Class to control the tft.
		The row numbering starts at 1.
		Calling writerow does not display anything. Also need to call display.
		'''
	def __init__(self, rowcount=4):
		self.rowlength = 22
		self.disp = TFT.ILI9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))
		self.disp.begin()
		self.disp.clear()	# black
		self.old_text = [' ' for i in range(5)]	# used for clearing oled text
#		self.font = ImageFont.load_default()
		self.font = [ImageFont.load_default() for i in range(5)]
		self.fontsize = [24 for i in range(rowcount)]		# default font size
#		self.fontsize[1] = 36		
		self.font[0] = ImageFont.truetype('binary/Hack-Regular.ttf',self.fontsize[0])
		self.font[1] = ImageFont.truetype('binary/Hack-Regular.ttf',self.fontsize[1])
		self.font[2] = ImageFont.truetype('binary/Hack-Regular.ttf',self.fontsize[2])
		self.font[3] = ImageFont.truetype('binary/Hack-Regular.ttf',self.fontsize[3])
		self.offset = [0 for i in range(rowcount)]
		# setup the pixel offset for each row
		for i in range (1,rowcount):
			self.offset[i] = self.offset[i-1]+self.fontsize[i]
	
	def _draw_rotated_text(self, image, text, position, angle, font, fill=(255,255,255)):
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
		thisrow = rownumber - 1
		rotation = 90
		if rotation == 0:
			xpos = 0
			ypos = self.offset[thisrow]
		else:
			ypos = 0
			xpos = self.offset[thisrow]
		thisfont = self.font[thisrow]
		if clear == True:
			self._draw_rotated_text(self.disp.buffer, self.old_text[thisrow], (xpos, ypos), rotation, thisfont, fill=(0,0,0))
		self._draw_rotated_text(self.disp.buffer, string, (xpos, ypos), rotation, thisfont, fill=(255,255,255))
		self.old_text[thisrow] = string
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
			self.writerow(1, date_now, True)	
			self.writerow(2, time_now+' ', True)	
			self.writerow(3, '012345678901234567890', True)	
			self.writerow(4, 'Row 4', True)	
			self.display()
			time.sleep(1)
		return(0)
	
	def display(self):
		self.disp.display()
		return(0)

if __name__ == "__main__":
	print 'TFT test'		
	MyScreen = Screen()
	MyScreen.show_time()
	