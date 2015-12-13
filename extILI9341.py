#!/usr/bin/python
# Extending the Adafruit ILI9341 python library.

import ILI9341

class extendedILI9341(ILI9341):
	def __init__(self):
		ILI9341.__init__()
		
	
	def small_display_update(self, x=0, y=0, x1=20, y1=20):
		# to speed things up, just update a fraction of the display.
		self.set_window(x,y,x1,y1)
		pixelbytes = list(image_to_data(image))
		self.data(pixelbytes)					# actually write the data.
		return(0)
		
	