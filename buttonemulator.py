#!/usr/bin/python
# buttonemulator.py

import os, time, datetime
import pygame
from pygame.locals import *
import threading, Queue

class Buttons(threading.Thread):

	def __init__(self):
		self.Event = threading.Event()
#		self.threadLock = threading.Lock()
		threading.Thread.__init__(self, name='buttonemulator')
		self.q = Queue.Queue(maxsize=6)

	def run(self):
		myevent = False
		while not myevent:
			for event in pygame.event.get():
				if event.type == QUIT:
					self.Event.set()
				if event.type == MOUSEBUTTONDOWN:
					self._button_click_test()
			myevent = self.Event.wait(.5)	# wait for this timeout or the flag being set.
		self.cleanup()

	def _button_click_test(self):
		mousex, mousey = pygame.mouse.get_pos()
		if mousey > 80 and mousey < 100:
			if mousex > 20 and mousex < 40:
				print 'next button click'
			if mousex > 50 and mousex < 70:
				print 'stop button click'
			if mousex > 80 and mousex < 100:
				print 'vol+ button click'
			if mousex > 110 and mousex < 130:
				print 'vol- button click'
			if mousex > 140 and mousex < 160:
				print 'quit button click'
				self.Event.set()
		else:
			print 'click'

	def master_loop(self):
		timeout = datetime.timedelta(seconds=TIMEOUT)
		start_time = datetime.datetime.now()	 # need to complete this!!
		runner = True
		while runner:
			pygame.time.wait(500)
			now = datetime.datetime.now()	 # need to complete this!!
			if (now - start_time) > timeout:
				runner = False
			else:
				runner = self._chk_for_quit()

	def _chk_for_quit(self):
		for event in pygame.event.get():
			if event.type == QUIT:
				return(False)
			if event.type == MOUSEBUTTONDOWN:
				self._button_click_test()
		return(True)

	def cleanup(self):
		pass

if __name__ == "__main__":
	print 'Button emulator test'
	myEmulator = Buttons()
	myEmulator.start()
