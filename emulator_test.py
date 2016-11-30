#!/usr/bin/python
# emulator_test.py

import os, time, datetime
import emulator_multi

def test_emulator():
    myEmulator = emulator_multi.Display()
    myEmulator.start()
    time.sleep(15)
    myEmulator.terminate()
#    myEmulator.join()

if __name__ == '__main__':
#    freeze_support()
    test_emulator()
