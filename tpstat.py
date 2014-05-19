#!/usr/bin/python2
#

import time
import curses
from os import statvfs
from procfs import Proc

# This stuff is good canditate for __init__
proc = Proc()

stdscr = curses.initscr()
curses.noecho()
curses.cbreak() # handle input before receiving newlines

sectorSize = statvfs("/dev/sdc").f_bsize
print "sectorSize: " , sectorSize

#TODO: use list of devices and gather from each
try:
	val = proc.diskstats.sdc.read.sectors
	delta = 0;

	while 1:
		lastVal = val
		time.sleep(1)
		val = proc.diskstats.sdc.read.sectors
		delta = (val - lastVal) * sectorSize
		print(delta)


# TODO: catch block or something?
except KeyboardInterrupt:
	print "In except block"
	#time.sleep(1)
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()
