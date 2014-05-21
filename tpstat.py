#!/usr/bin/python2
#

import time
import curses
from os import statvfs
from procfs import Proc

multiplier = 0.1
k = 1024
#multiplier = 1

def formatReadableAbs(bytes):
	ret = str(bytes) + "\tbytes\t"
	if bytes >= k:
		ret = str(bytes / k) + "\tKB\t"
	if bytes >= k**2:
		ret = str(bytes / k**2) + "\tMB\t"
	if bytes >= k**3:
		ret = str(bytes / k**3) + "\tGB\t"
	if bytes >= k**4:
		ret = str(bytes / k**4) + "\tTB\t"
	if bytes >= k**5:
		ret = str(bytes / k**5) + "\tExabytes\t"
	return ret


def formatReadableRate(bytes):
	bytesPerSecond = bytes / multiplier
	ret = str(bytesPerSecond) + "\tbytes/sec\t"
	if bytesPerSecond >= k:
		ret = str(bytesPerSecond / k) + "\tKB/sec\t"
	if bytesPerSecond >= k**2:
		ret = str(bytesPerSecond / k**2) + "\tMB/sec\t"
	if bytesPerSecond >= k**3:
		ret = str(bytesPerSecond / k**3) + "\tGB/sec\t"
	if bytesPerSecond >= k**4:
		ret = str(bytesPerSecond / k**4) + "\tTB/sec\t"
	if bytesPerSecond >= k**5:
		ret = str(bytesPerSecond / k**4) + "\tHello future person!"
	return ret

# This stuff is good canditate for __init__
proc = Proc()

stdscr = curses.initscr()
curses.noecho()
curses.cbreak() # handle input before receiving newlines

sectorSize = statvfs("/dev/sda5").f_bsize
print "sectorSize: " , sectorSize

#TODO: use list of devices and gather from each
try:
	total = 0
	peak = 0
	avg = 0
	count = 0
	val = proc.diskstats.sda5.read.sectors
	delta = 0;

	while 1:
		count += 1
		total += delta
		avg = total / count
		if delta > peak:
			peak = delta

		lastVal = val
		time.sleep(1 * multiplier)
		val = proc.diskstats.sda5.read.sectors
		delta = (val - lastVal) * sectorSize
		#print(delta)
#stdscr.clear()
		stdscr.addstr(0, 0, "Cur:\t" + formatReadableRate(delta))
		stdscr.addstr(1, 0, "Avg:\t" + formatReadableRate(avg))
		stdscr.addstr(2, 0, "Peak:\t" + formatReadableRate(peak))
		stdscr.addstr(3, 0, "Total:\t" + formatReadableAbs(total))
		stdscr.refresh()


# TODO: catch block or something?
except KeyboardInterrupt:
	print "In except block"
	#time.sleep(1)
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()
