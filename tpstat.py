#!/usr/bin/python2
#

import traceback
import time
import curses
from os import statvfs,sys
from procfs import Proc

#interval = 0.1
k = 1024
interval = .1

# This stuff is good canditate for __init__
# TODO: clean this up; these are globals accessed from 
# pretty much everywhere.
proc = Proc()
stdscr = curses.initscr()
curses.noecho()
curses.cbreak() # handle input before receiving newlines

def getMounts (device):
	"work in progress, will eventually look up mounts per device"
	print "getMounts"
	ret = []
	ret.append("/foo")
	node = "/dev/" + device
	print node

	p = Proc()

#for mount in p.mounts.device(node):
#for mount in p.mounts:
#		print mount
#		ret.append(str(mount))

#	return ret

class DeviceStats(object):
	"parent class for different device types" 
	def __init__(self, position, dev):
		if type(self) == DeviceStats:
			raise Exception ("DeviceStats is an abstract class")
		self.lines = 6 # should be overrideable
		self.position = position
		self.dev = dev
		self.count = 0
		self.fetch(dev) # TODO: inheritance. if I call this here in super's init
					 # will it call the child method?
		#TODO: encapsulate, add write stats
		self.lastVal = self.val
		self.delta = 0
		self.avg = 0
		self.peak = 0
		self.total = 0

	def fetch(self, dev):
		"virtual method to fetch device-specific stats from procfs"
		pass



class NetDeviceStats(DeviceStats):
	"per-interface statistics and display methods"
	def __init__(self, position, dev):
		super(NetDeviceStats, self).__init__(position, dev)

	def fetch(self, dev):
		# needs dev as an arg to avoid circular dependencies in
		# parent and subclass ctors
		"fetch net device stat value from procfs"
		self.val = proc.net.dev[dev].receive.bytes
	
	def calculate (self):
		self.count += 1
		self.fetch(self.dev)
		self.delta = self.val - self.lastVal
		self.total += self.delta
		self.avg = self.total / self.count
		if self.delta > self.peak:
			self.peak = self.delta
		self.lastVal = self.val

	def printStats (self):
		startLine = self.position * self.lines
		stdscr.addstr(startLine, 0, "interface " + self.dev + "\t ")
		stdscr.addstr(startLine+1, 0, "Cur:\t" + formatReadableRate(self.delta))
		stdscr.addstr(startLine+2, 0, "\t" + formatReadableRate(self.delta, True))
		stdscr.addstr(startLine+3, 0, "Avg:\t" + formatReadableRate(self.avg))
		stdscr.addstr(startLine+4, 0, "Peak:\t" + formatReadableRate(self.peak))
		stdscr.addstr(startLine+5, 0, "Total:\t" + formatReadableAbs(self.total))

class BlockDeviceStats(DeviceStats):
	"per-device statistics and methods for displaying them"

	def __init__(self, position, dev):
		self.sectorSize = statvfs("/dev/" + dev).f_bsize
		super(BlockDeviceStats, self).__init__(position, dev)
		self.mounts = ""
		#self.mounts = getMounts(self.dev)

	def fetch(self, dev):
		"fetch block dev stats from procfs"
		self.val = proc.diskstats[dev].read.sectors * self.sectorSize

	def calculate (self):
		self.count += 1
		self.fetch(self.dev)
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


def formatReadableRate(bytes, bits = False):
	bytesPerSecond = float(bytes) / interval
	ret = str(bytesPerSecond) + "\tbytes/sec\t"
	if bytesPerSecond >= k:
		ret = str(bytesPerSecond / k) + "\tKB/sec\t"
	if bytesPerSecond >= k**2:
		if bits:
			ret = str((bytesPerSecond / k**2) * 8) + "\tMbps\t"
		else:
			ret = str(bytesPerSecond / k**2) + "\tMB/sec\t"
	if bytesPerSecond >= k**3:
		ret = str(bytesPerSecond / k**3) + "\tGB/sec\t"
	if bytesPerSecond >= k**4:
		ret = str(bytesPerSecond / k**4) + "\tTB/sec\t"
	if bytesPerSecond >= k**5:
		ret = str(bytesPerSecond / k**4) + "\tHello future person!"
	return ret



#TODO: use list of devices and gather from each
try:
	devList = []
	count = 0
	if len(sys.argv) == 1: # TODO:print stderr correctly
		print "Error: need a device list on the command line"

	for arg in sys.argv:
		if count > 0: # LOL
			print "adding " + arg
			devList.append(BlockDeviceStats(count, arg))
		count += 1

	devList.append(NetDeviceStats(count, "p5p1"))
	count += 1
		
#	devList.append(BlockDeviceStats(0, "sdc")) 
#	devList.append(BlockDeviceStats(1, "sda3")) 

#	ds = BlockDeviceStats(0, "sdc") 

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
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()
	print(traceback.format_exc())
	#time.sleep(1)
#curses.nocbreak(); stdscr.keypad(0); curses.echo()
#curses.endwin()

#except:
finally:
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()
