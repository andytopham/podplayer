#!/usr/bin/python
# keyboardpoller.py
# From an idea at...
# https://mail.python.org/pipermail/tutor/2001-November/009936.html

import sys
import threading

# this is to signal when the key_pressed flag has useful data,
# it will be "set" to indicate that the key_pressed flag has been set
# accordingly
data_ready = threading.Event()
matrix = {'n':'Next', 'p':'Prev'}
 
class KeyboardPoller( threading.Thread ) :
	def __init__(self):
		self.Event = threading.Event()
		threading.Thread.__init__(self, name='mykeyboard')
		self.ch = ''
#		self.logger = logging.getLogger(__name__)
				
	def run(self):
		print 'Starting keyboard manager.'
		myevent = False
		while not myevent:
			self.ch = sys.stdin.read( 1 ) 
			if self.ch != '\n':
				print 'Got',self.ch
				print 'Decoded:', self.decode(self.ch)
				if self.ch == 'x':
					self.Event.set()
			myevent = self.Event.wait(.5)	# wait for this timeout or the flag being set.
		print 'Keyboard manager exiting'
	
	def decode(self, ch):
		if ch in matrix:
			return(matrix[ch])
		else:
			return('Invalid char:'+ch)
		
if __name__ == "__main__" :
	poller = KeyboardPoller()
	poller.start()
	print 'poller started'
	if poller.ch != '':
		print 'Polled:', poller.ch
	print 'Main prog exiting'
	