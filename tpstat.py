#!/usr/bin/python2
#

import time
import curses
from os import statvfs,sys
from procfs import Proc

#interval = 0.1
k = 1024
interval = .3

def getMounts (device):
	print "getMounts"
	ret = []
	ret.append("/foo")
	node = "/dev/" + device
	print node

	p = Proc()

#for mount in p.mounts.device(node):
	for mount in p.mounts:
		print mount
#		ret.append(str(mount))

	return ret


class deviceStats:
	"per-device statistics and methods for displaying them"

	def __init__(self, position, dev):
		self.lines = 6 # all fields plus a newline
		self.position = position
		self.dev = dev
		self.mounts = getMounts(self.dev)
		self.sectorSize = statvfs("/dev/" + self.dev).f_bsize
		self.count = 0
		self.val = proc.diskstats[self.dev].read.sectors * self.sectorSize
		self.lastVal = self.val
		self.delta = 0
		self.avg = 0
		self.peak = 0
		self.total = 0
#		print "sectorSize: " , self.sectorSize

	def calculate (self):
		self.count += 1
		self.val = proc.diskstats[self.dev].read.sectors * self.sectorSize
		self.delta = (self.val - self.lastVal) 
		self.total += self.delta
		self.avg = self.total / self.count #TODO some math with interval for rate
		if self.delta > self.peak:
			self.peak = self.delta

		self.lastVal = self.val
		#time.sleep(1 * interval)

	def printStats (self):
		startLine = self.position * self.lines
		stdscr.addstr(startLine, 0, "/dev/" + self.dev + "\t" + " " + str(self.mounts));
		stdscr.addstr(startLine+1, 0, "Cur:\t" + formatReadableRate(self.delta))
		stdscr.addstr(startLine+2, 0, "Avg:\t" + formatReadableRate(self.avg))
		stdscr.addstr(startLine+3, 0, "Peak:\t" + formatReadableRate(self.peak))
		stdscr.addstr(startLine+4, 0, "Total:\t" + formatReadableAbs(self.total))
		


def formatReadableAbs(bytes):
	ret = str(bytes) + "\tbytes\t"
	if bytes >= k:
		ret = str(float(bytes) / k) + "\tKB\t"
	if bytes >= k**2:
		ret = str(float(bytes) / k**2) + "\tMB\t"
	if bytes >= k**3:
		ret = str(float(bytes) / k**3) + "\tGB\t"
	if bytes >= k**4:
		ret = str(float(bytes) / k**4) + "\tTB\t"
	if bytes >= k**5:
		ret = str(float(bytes) / k**5) + "\tExabytes\t"
	return ret


def formatReadableRate(bytes):
	bytesPerSecond = float(bytes) / interval
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

#TODO: use list of devices and gather from each
try:
	devList = []
	count = 0
	if len(sys.argv) == 1: # TODO:print stderr correctly
		print "Error: need a device list on the command line"
		throw
		
	for arg in sys.argv:
		if count > 0: # LOL
			print "adding " + arg
			devList.append(deviceStats(count, arg))
		count += 1
		
#	devList.append(deviceStats(0, "sdc")) 
#	devList.append(deviceStats(1, "sda3")) 

#	ds = deviceStats(0, "sdc") 

	while 1:
		time.sleep(1 * interval)
#stdscr.clear()
		for ds in devList:
			ds.calculate()
			ds.printStats()
			stdscr.refresh()

except Exception, e:
	print "In except block"
	print e
	#time.sleep(1)
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()

except:
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()
