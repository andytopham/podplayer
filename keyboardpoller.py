#!/usr/bin/python
# keyboardpoller.py
# From an idea at...
# https://mail.python.org/pipermail/tutor/2001-November/009936.html
# But better, is to use the readchar library for single char input at....
# https://github.com/magmax/python-readchar
# Need to do: sudo pip install readchar

import sys, time, logging
import threading
import readchar

# this is to signal when the key_pressed flag has useful data,
# it will be "set" to indicate that the key_pressed flag has been set
# accordingly

matrix = {'n':'Next', 
		'p':'Prev', 
		's':'Stop', 
		'v':'VolumeUp',
		'w':'VolumeDown',
		'x':'Exit'}
 
class KeyboardPoller( threading.Thread ) :
	def __init__(self):
		self.Event = threading.Event()
		threading.Thread.__init__(self, name='mykeyboard')
		self.logger = logging.getLogger(__name__)
		self.ch = ''
		self.next = False
		self.stop = False
		self.prev = False
		self.volup = False
		self.voldown = False
		self.exit = False
		self.command = False
		
	def run(self):
		print 'Starting keyboard manager.'
		myevent = False
		while not myevent:
			self.ch = readchar.readchar()
			decoded = self.decode(self.ch)
			print 'Keyboard: Got',self.ch, '. Decoded to:', decoded
#			self.logger.info('Keyboard: Got'+self.ch+'. Decoded to:'+decoded)
			if self.ch in matrix:
				self.command = True			
			if self.ch == 'n':
				self.next = True
			if self.ch == 's':
				self.stop = True
			if self.ch == 'p':
				self.prev = True
			if self.ch == 'v':
				self.volup = True
			if self.ch == 'w':
				self.voldown = True
			if self.ch == 'x':
				self.exit = True
				self.Event.set()
			while self.command:
				pass
			myevent = self.Event.wait(.5)	# wait for this timeout or the flag being set.
		print 'Keyboard manager exiting'
		
	def cleanup(self):
		self.Event.set()
		
	def decode(self, ch):
		if ch in matrix:
			return(matrix[ch])
		else:
			return('Invalid char:'+ch)
		
if __name__ == "__main__" :
	logging.basicConfig(filename='log/kbd.log', filemode='w', level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+
					". Running keyboardpoller class as a standalone app")

	print 'Scanning keyboard for commands to run.'
	print 'Options: n s p v w x'
	poller = KeyboardPoller()
	poller.start()
	time.sleep(1)
	print 'Main prog exiting'
	print
	