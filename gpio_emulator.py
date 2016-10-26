#!/usr/bin/python
# gpio_emulator.py

# import os
import time
# import pygame
# from pygame.locals import *
import emulator

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255,255,255)
BLACK = (0, 0, 0)
ROWHEIGHT = 20

class Gpio():

    def __init__(self):
        print 'starting gpio emulator'
        self.next = False
        self.stop = False
        self.vol = 0
        self.chgvol_flag = False
        


    def cleanup(self):
        print 'cleaning up gpio emulator'

#    def test(self):
#        print 'test'

if __name__ == "__main__":
    myEmulator = emulator.Display()
    myEmulator.buttons()
    myEmulator.test()
    myEmulator.display()
    myEmulator.master_loop()
#    time.sleep(5)
