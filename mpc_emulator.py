#!/usr/bin/python
# mpc_emulator.py

import logging

class Mpc:
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.logger.info("Starting mpc emulator class")
		#initialise the variables
