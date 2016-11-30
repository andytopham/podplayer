#!/usr/bin/python
# uoled_emulator.py

import os, time, datetime
import pygame
from pygame.locals import *
import Queue
import multiprocessing

TIMEOUT = 10	# seconds
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0,255,255)
VIOLET = (255,0,255)
WHITE = (255,255,255)
BLACK = (0, 0, 0)
ROWHEIGHT = 20
ROWCOUNT = 4

class Display(multiprocessing.Process):

	def __init__(self):
#		self.Event = threading.Event()
#		multiprocessing.freeze_support()
		multiprocessing.Process.__init__(self, name='myprocess')
		self.q = multiprocessing.Queue(maxsize=6)
		x = 20
		y = 300
		os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)
		pygame.init()
		self.xmax = 220
		self.ymax = 160
		self.ytop = 100
		self.screen = pygame.display.set_mode((self.xmax, self.ymax))
		pygame.display.set_caption('uoled emulator')
		self.background = pygame.Surface(self.screen.get_size())
		self.background = self.background.convert()
		self.background.fill(BLACK)
		self.buttons()
		self.last_prog_row = ROWCOUNT - 2
		self.oldtext = []
		for i in range(ROWCOUNT):
			self.oldtext.append('')
		self.button = ''

	def run(self):
		myevent = False
		while not myevent:
			while not self.q.empty():
				entry = self.q.get()
				self.writerow(entry[0], entry[1])
				self.q.task_done()
#			myevent = self.Event.wait(.5)	# wait for this timeout or the flag being set.
#			self.master_checks()
		self.cleanup()

	def buttons(self):
		ytop = self.ytop
		pygame.draw.rect(self.background, GREEN ,(20,ytop,20,20))
		pygame.draw.rect(self.background, YELLOW ,(50,ytop,20,20))
		pygame.draw.rect(self.background, BLUE ,(80,ytop,20,20))
		pygame.draw.rect(self.background, CYAN ,(110,ytop,20,20))
		pygame.draw.rect(self.background, WHITE ,(140,ytop,20,20))
		font = pygame.font.Font(None, 12)
		text = font.render('Next', 1, BLACK)
		self.background.blit(text, (20,ytop+5))
		text = font.render('Stop', 1, BLACK)
		self.background.blit(text, (50,ytop+5))
		text = font.render('Vol+', 1, BLACK)
		self.background.blit(text, (80,ytop+5))
		text = font.render('Vol-', 1, BLACK)
		self.background.blit(text, (110,ytop+5))
		text = font.render('Quit', 1, BLACK)
		self.background.blit(text, (140,ytop+5))
		self.screen.blit(self.background, (0, 0))
		self.display()

	def writerow(self, rownumber, string):
		if rownumber > ROWCOUNT-1:
			print 'Row number exceeded:', rownumber
			return(1)
		pygame.draw.rect(self.background, BLACK ,(0,rownumber*ROWHEIGHT,self.xmax,ROWHEIGHT))	# delete old text
		ytop = 100
		ypos = ROWHEIGHT / 2 + (rownumber) * ROWHEIGHT
		font = pygame.font.Font(None, 24)
		text = font.render(string, 1, WHITE)
		textpos = text.get_rect(centery = ypos)
		self.background.blit(text, textpos)
		self.screen.blit(self.background, (0, 0), (0,0,self.xmax,ytop))
		self.oldtext[rownumber] = string
		self.display()

	def display(self):
		pygame.display.update()
		return(0)

	def test(self):
		self.writerow(0,'Emulator test.')
		self.writerow(1,'01234567890')

	def _button_click_test(self):
		mousex, mousey = pygame.mouse.get_pos()
		if mousey > self.ytop and mousey < self.ytop+20:
			if mousex > 20 and mousex < 40:
				print 'next button click'
				self.button = 'Next'
				return(True)
			if mousex > 50 and mousex < 70:
				print 'stop button click'
			if mousex > 80 and mousex < 100:
				print 'vol+ button click'
			if mousex > 110 and mousex < 130:
				print 'vol- button click'
			if mousex > 140 and mousex < 160:
				print 'quit button click'
#				self.Event.set()
				return(False)
			return(True)
		else:
			print 'click'
			return(True)

	def master_checks(self):
		timeout = datetime.timedelta(seconds=TIMEOUT)
		start_time = datetime.datetime.now()	 # need to complete this!!
		runner = True
		now = datetime.datetime.now()	 # need to complete this!!
		if (now - start_time) > timeout:
			print 'Timeout'
			myEmulator.q.put([0, 'Timeout'])
			runner = False
		else:
			runner = self._chk_for_quit()
		if self.button == 'Next':
			myEmulator.q.put([0, 'Next button'])
		return(runner)

	def master_loop(self):
		timeout = datetime.timedelta(seconds=TIMEOUT)
		start_time = datetime.datetime.now()	 # need to complete this!!
		runner = True
		while runner:
			pygame.time.wait(500)
			now = datetime.datetime.now()	 # need to complete this!!
			if (now - start_time) > timeout:
				print 'Timeout'
				runner = False
			else:
				runner = self._chk_for_quit()
			if self.button == 'Next':
				myEmulator.q.put([0, 'Next button'])
			while not self.q.empty():
				entry = self.q.get()
				self.writerow(entry[0], entry[1])
#				self.q.task_done()
		print 'Exiting master loop'
		time.sleep(1)
		self.cleanup()

	def _chk_for_quit(self):
		for event in pygame.event.get():
			if event.type == QUIT:
				return(False)
				self.Event.set()
			if event.type == MOUSEBUTTONDOWN:
				return(self._button_click_test())
		return(True)

	def info(self):
		return(ROWCOUNT,20)

	def write_radio_extras(self, clock, temperature):
		self.q.put([ROWCOUNT-1,'{0:5s}{1:7.1f}^C'.format(clock.ljust(10),float(temperature))])
		return(0)

	def write_button_labels(self, next, stop):
		return(0)

	def cleanup(self):
		print 'Quiting pygame'
		pygame.quit()

if __name__ == "__main__":
	print 'Emulator test'
	myEmulator = Display()
#	myEmulator.start()
#	print threading.enumerate()
	myEmulator.q.put([0, 'Emulator test'])
	myEmulator.master_loop()
	time.sleep(2)
	myEmulator.q.put([0, 'Emulator test'])
	time.sleep(2)
	myEmulator.q.put([1, 'Second row. This is a very long row.'])

#	myEmulator.test()
#	myEmulator.buttons()
#	myEmulator.display()
#	myEmulator.master_loop()
#	time.sleep(10)
#	myEmulator.Event.set()
#	myEmulator.cleanup()
