#!/usr/bin/python
''' 
  comms - the routines for using sockets with radio.
  Protocol:
  Socket	Master					Slave
  sock		Receive connection		Send request
  sock2		Send ack				Receive ack
  sock3		Send cmd				Receive cmd
  
  Twisted: sudo apt-get install python-twisted
 
'''
import socket
import logging
import time
import datetime
import select		# used to wait for i/o completion
import config
MSGLEN = 5

class Comms:
	'''demonstration class only
	  - coded for clarity, not efficiency
	'''

	def __init__(self, sock=None):	
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		else:
			self.sock = sock
		self.sock.settimeout(200.0)		# timeout seconds
		self.sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.port = 12346				# my random number
		self.msgport = 55655
		self.cmdport = 61788
		self.msg = 'Test'
		self.timeout = 0				# seconds
	
	# Phase 1 of the protocol

	def registerserversetup(self):
		''' Just setup a server to get registering requests and collect addresses for later.
		So far this is only collecting a single client address.
		Needs restructuring for multiple clients (how to collect addresses later...)'''
		host = ''							# symbolic name for all available interfaces
		try:
			self.sock.bind((host,self.port))
			self.sock.listen(1)
			while True:
				conn,addr = self.sock.accept()
				print "Remote client:",addr[0]," registered"
				time.sleep(1)
				data = conn.recv(1024)
				self.sock.close()
				print 'Data: ',data
#			print "Phase 1 complete"
			return(addr[0])
		except socket.timeout:
			print "** Timeout - no clients tried to connect **"
			return(0)
			
	def registerclient(self,serveraddress,data):
		'''This goes wtih registerserversetup. It is the client part. 
		Used to send a msg to the server so that the server knows about us.''' 
		host = serveraddress				# address of server
#		mySocket.connect(host,self.port)
		self.sock.connect((host, self.port))
#		self.connect(host,self.port)
		print "Registering...",
		self.sock.sendall(data)
		print "Sent"
		self.sock.close()
#		print "Phase 1 complete"
		return(0)

	# Phase 2 of the protocol
	def setuplistener(self):
#		self.sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		host = ''
		self.sock2.bind((host,self.msgport))
		self.sock2.listen(5)
		self.conn,addr = self.sock2.accept()
		data = self.conn.recv(1024)
		print "Command received:", data
		self.sock2.close()
		print "Phase 2 complete"
		return(0)

	def send2cmd(self,addr,cmd):
		'''Just send a command (based on button push) to a pre-existing connection.
		This only works when we have already setup the link with setupsender.'''
		if addr != 0:		# this is only to send if we are the master
			self.sock2.connect((addr, self.msgport))
			print "Sending...",cmd,
			self.sock2.sendall(cmd)
			print "...Sent"
			self.sock2.close()
			print "Phase 2 complete"
		return(0)
	
	# Phase 3 of the protocol
	def setupsender(self,addr):
		'''Setup a pipe for subseqent commands to be sent down, using sendcmd().'''
		print "Phase 3: setting up sender"
		self.sock3.connect((addr, self.cmdport))
	
	def sendcmd(self,addr,cmd):
		'''Just send a command (based on button push) to a pre-existing connection.
		This only works when we have already setup the link with setupsender.'''
		if addr != 0:		# this is only to send if we are the master
			print "Phase 3: Sending...",cmd,
			self.sock3.sendall(cmd)
			print "...Sent"
	#		self.sock3.close()
			return(0)
	
	def cmdlistener(self):
		''' Just initialise the listener'''
		host = ''
		self.sock3.setblocking(0)		# non-blocking, so that it will not block forever
		self.sock3.bind((host,self.cmdport))
		self.sock3.listen(5)
#		self.sock3.settimeout(2.0)
		noconnect=1
		while noconnect:
			try:
				self.conn,addr = self.sock3.accept()
				noconnect=0
			except socket.error:
				print "..."
			time.sleep(.5)
#		self.sock3.settimeout(0.1)
		return(self.conn)
	
	def fetchcmd(self,conn):
#		self.sock3.settimeout(0.1)
		try:
#			data = conn.recv(1024)
			data = self.sock3.recv(1024)
			print "Command received:", data
			return(data)
		except socket.timeout:
			print "timeout"
			return(0)
	
	
	def fetch3cmd(self):		# this one not being used right now.
		''' actually grab the cmd'''
		print "Fetching cmd"
		selecttimeout=30
		readerlist = [self.sock3]
		try:
			readers,writers,errors = select.select(readerlist,[],[],selecttimeout)
			for s in readers:
				if s is self.sock3:
					self.conn,addr = self.sock3.accept()
					readerlist.append(self.conn)
					print "Connection from ",addr
				else:
					data = s.recv(1024)
					print "Command received:", data
					return(data)
		except:
			print "No data"
			return(0)
		
	def sendtoclient(self,command):
		self.sock3.sendall(command)
		return(0)
	
		
if __name__ == "__main__":
	
	'''Called if this file is called standalone. Then just runs a selftest. '''
	print "Running socket class as a standalone app"
	logging.basicConfig(filename='log/socket.log',
						filemode='w',
						level=logging.WARNING)	#filemode means that we do not append anymore
#	Default level is warning, level=logging.INFO log lots, level=logging.DEBUG log everything
	logging.warning(datetime.datetime.now().strftime('%d %b %H:%M')+". Running socket class as a standalone app")

	# This demo just does a handshake back and forwards.
	mySocket = Comms()
	if True:
		print "I am a server"
		slave = mySocket.registerserversetup()
#		time.sleep(2)
#		mySocket.sendcmd(slave,"Comms prog test string")
	else:
		print "I am a client"
		mySocket.registerclient('192.168.1.149','22.2')
#		mySocket.setuplistener()
		