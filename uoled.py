''' uoled.py
	Completely replaces oled.py.
	Called by infodisplay.py
	Now threaded.
	The text to be written is placed in a queue, 
	and then the run method works through this.
'''
import gaugette.ssd1306
import time, sys, logging, datetime
from time import gmtime, strftime
import threading, Queue

# Setting some variables for our reset pin etc.
# This numbering comes from wiringpi.
#RESET_PIN = 5		# gpio24	pin18
#DC_PIN    = 4		# gpio23	pin16
#RESET_PIN = 6		# gpio25	pin22
RESET_PIN = 15
DC_PIN    = 16
#DC_PIN    = 0		# gpio17	pin11	
ROWLENGTH = 20
LAST_PROG_ROW = 2

LOGFILE = 'log/uoled.log'

class Screen(threading.Thread):
	def __init__(self, rowcount = 4):
		self.Event = threading.Event()
		self.threadLock = threading.Lock()
		threading.Thread.__init__(self, name='myuoled')
		self.q = Queue.Queue(maxsize=6)
		self.logger = logging.getLogger(__name__)
		self.rowcount = rowcount
		self.rowlength = ROWLENGTH
		self.last_prog_row = LAST_PROG_ROW
#		self.last_prog_row = rowcount-1
		self.led = gaugette.ssd1306.SSD1306(reset_pin=RESET_PIN, dc_pin=DC_PIN)
		self.led.begin()
		self.led.clear_display() # This clears the display but only when there is a led.display() as well!
		time.sleep(1)
		self.led.display()
		time.sleep(1)
		self.led.draw_text2(0,0,'Init uoled',1)
		self.led.display()
		time.sleep(1)
	
	def run(self):
		self.logger.info('Starting uoled queue manager.')
		myevent = False
		while not myevent:
			while not self.q.empty():
				entry = self.q.get()
				self.writerow(entry[0], entry[1])	
				self.q.task_done()
			myevent = self.Event.wait(.5)	# wait for this timeout or the flag being set.
		self.logger.info('Uoled exiting')
	
	def clear(self):
		self.led.clear_display() # This clears the display but only when there is a led.display() as well!
		time.sleep(.5)
		self.led.display()
		time.sleep(1)		# this really is needed!
	
	def info(self):
		return(self.rowcount, self.rowlength)
		
	def write_button_labels(self, next, stop):
		# These are the botton labels. No labels with small display.
		if next == True:
			self.q.put([0,'Next                '])
		if stop == True:
			self.q.put([0,'Stop                '])
			return(0)
		
	def write_radio_extras(self, clock, temperature):
		self.q.put([self.rowcount-1,'{0:5s}{1:7.1f}^C'.format(clock.ljust(self.rowlength-9),float(temperature))])		
		return(0)
		
	def writerow(self, row, string):
		if row < self.rowcount:
			if row == 0:
				x = 0
				y = 0
			if row == 1:
				x = 0
				y = 8
			if row == 2:
				x = 0
				y = 16
			if row == 3:
				x = 0
				y = 24
			self.led.draw_text2(x,y,string,1)
			self.led.display()
		return(0)
		
if __name__ == "__main__":
	print "Running uoled class as a standalone app"
	logging.basicConfig(filename=LOGFILE, filemode='w', level=logging.INFO)
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running uoled class as a standalone app")
	
	print 'Testing uoled functionality.'
	myScreen = Screen()
	myScreen.q.put([1, 'Uoled test'])
	myScreen.start()
	myScreen.write_button_labels(True, True)
	time.sleep(2)
	clock = time.strftime("%R")
	myScreen.write_radio_extras(clock, '9.9')
	myScreen.q.put([2,'Test passed.'])
	time.sleep(5)
	print 'Ending process'
	myScreen.Event.set()
	print 'Exit main prog'
