#!/usr/bin/python
#

import traceback
import getopt
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
class StatTracker(object):
	def __init__(self, initialVal):
		self.count = 0
		self.val = initialVal;
		self.lastVal = self.val
		self.delta = 0
		self.avg = 0
		self.peak = 0
		self.total = 0

	def calculate(self, newVal):
		self.count += 1
		self.val = newVal
		self.delta = self.val - self.lastVal
		self.total += self.delta
		self.avg = self.total / self.count
		if self.delta >self.peak:
			self.peak = self.delta
		self.lastVal = self.val
		

class DeviceStats(object):
	"parent class for different device types" 
	def __init__(self, position, dev):
		if type(self) == DeviceStats:
			raise Exception ("DeviceStats is an abstract class")
		self.lines = 11 # should be overrideable
		self.position = position
		self.dev = dev

		self.readTracker = StatTracker(self.fetchRead())
		self.writeTracker = StatTracker(self.fetchWrite())


	def fetchRead(self):
		"virtual method to fetch device-specific stats from procfs"
		pass
	def fetchWrite(self):
		"virtual method to fetch device-specific stats from procfs"
		pass

	def calculate (self):
		self.readTracker.calculate(self.fetchRead())
		self.writeTracker.calculate(self.fetchWrite())


class NetDeviceStats(DeviceStats):
	"per-interface statistics and display methods"
	def __init__(self, position, dev):
		super(NetDeviceStats, self).__init__(position, dev)

	def fetchRead(self):
		# needs dev as an arg to avoid circular dependencies in
		# parent and subclass ctors
		"fetch net device stat value from procfs"
		return proc.net.dev[self.dev].receive.bytes
	
	def fetchWrite(self):
		"fetch net device stat value from procfs"
		return proc.net.dev[self.dev].transmit.bytes

	def printStats (self):
		startLine = self.position * self.lines
		stdscr.addstr(startLine, 0, "interface " + self.dev + "\t ")
		stdscr.addstr(startLine+1, 0, "Rd Cur:\t\t" + formatReadableRate(self.readTracker.delta))
		stdscr.addstr(startLine+2, 0, "\t\t" + formatReadableRate(self.readTracker.delta, True))
		stdscr.addstr(startLine+3, 0, "Rd Avg:\t\t" + formatReadableRate(self.readTracker.avg))
		stdscr.addstr(startLine+4, 0, "Rd Peak:\t" + formatReadableRate(self.readTracker.peak))
		stdscr.addstr(startLine+5, 0, "Rd Total:\t" + formatReadableAbs(self.readTracker.total))

		stdscr.addstr(startLine+6, 0, "Wr Cur:\t\t" + formatReadableRate(self.writeTracker.delta))
		stdscr.addstr(startLine+7, 0, "\t\t" + formatReadableRate(self.writeTracker.delta, True))
		stdscr.addstr(startLine+8, 0, "Wr Avg:\t\t" + formatReadableRate(self.writeTracker.avg))
		stdscr.addstr(startLine+9, 0, "Wr Peak:\t" + formatReadableRate(self.writeTracker.peak))
		stdscr.addstr(startLine+10,0, "Wr Total:\t" + formatReadableAbs(self.writeTracker.total))

		stdscr.addstr(startLine+11,0, "R/W Cur:\t" + formatReadableRate(self.readTracker.delta
																	+	self.writeTracker.delta, True))
												

class BlockDeviceStats(DeviceStats):
	"per-device statistics and methods for displaying them"

	def __init__(self, position, dev):
		self.sectorSize = statvfs("/dev/" + dev).f_bsize
		super(BlockDeviceStats, self).__init__(position, dev)
		self.mounts = ""
		#self.mounts = getMounts(self.dev)

	def fetchRead(self):
		"fetch block dev stats from procfs"
		return proc.diskstats[self.dev].read.sectors * self.sectorSize
	def fetchWrite(self):
		return proc.diskstats[self.dev].write.sectors * self.sectorSize

	def printStats (self):
		startLine = self.position * self.lines
		stdscr.addstr(startLine, 0, "/dev/" + self.dev + "\t" + " " + str(self.mounts));
		stdscr.addstr(startLine+1, 0, "Rd Cur:\t\t" + formatReadableRate(self.readTracker.delta))
		stdscr.addstr(startLine+2, 0, "Rd Avg:\t\t" + formatReadableRate(self.readTracker.avg))
		stdscr.addstr(startLine+3, 0, "Rd Peak:\t" + formatReadableRate(self.readTracker.peak))
		stdscr.addstr(startLine+4, 0, "Rd Total:\t" + formatReadableAbs(self.readTracker.total))


		stdscr.addstr(startLine+5, 0, "Wr Cur:\t\t" + formatReadableRate(self.writeTracker.delta))
		stdscr.addstr(startLine+6, 0, "Wr Avg:\t\t" + formatReadableRate(self.writeTracker.avg))
		stdscr.addstr(startLine+7, 0, "Wr Peak:\t" + formatReadableRate(self.writeTracker.peak))
		stdscr.addstr(startLine+8, 0, "Wr Total:\t" + formatReadableAbs(self.writeTracker.total))

		stdscr.addstr(startLine+9, 0, "R/W Cur:\t" + formatReadableRate(self.readTracker.delta
																	+ self.writeTracker.delta, True))

def formatReadableAbs(bytes):
	ret = str(bytes) + "\t\tbytes\t"
	if bytes >= k:
		ret = str(float(bytes) / k) + "\tKB\t\t"
	if bytes >= k**2:
		ret = str(float(bytes) / k**2) + "\tMB\t\t"
	if bytes >= k**3:
		ret = str(float(bytes) / k**3) + "\tGB\t\t"
	if bytes >= k**4:
		ret = str(float(bytes) / k**4) + "\tTB\t\t"
	if bytes >= k**5:
		ret = str(float(bytes) / k**5) + "\tExabytes\t"
	return ret


def formatReadableRate(bytes, bits = False):
	bytesPerSecond = float(bytes) / interval
	ret = str(bytesPerSecond) + "\t\tbytes/sec\t"
	if bytesPerSecond >= k:
		ret = str(bytesPerSecond / k) + "\tKB/sec\t\t"
	if bytesPerSecond >= k**2:
		if bits:
			ret = str((bytesPerSecond / k**2) * 8) + "\tMbps\t\t"
		else:
			ret = str(bytesPerSecond / k**2) + "\tMB/sec\t\t"
	if bytesPerSecond >= k**3:
		ret = str(bytesPerSecond / k**3) + "\tGB/sec\t\t"
	if bytesPerSecond >= k**4:
		ret = str(bytesPerSecond / k**4) + "\tTB/sec\t\t"
	if bytesPerSecond >= k**5:
		ret = str(bytesPerSecond / k**4) + "\tHello future person!"
	return ret



#TODO: use list of devices and gather from each
try:
	blockDevs,netDevs = [],[]
	optlist, args = getopt.getopt(sys.argv[1:], "b:i:t:")
#blockDevs = []
	print str(optlist)+str(args)
	for i in optlist:
		opt = i[0]
		arg = i[1]
		print "opt is "	+ str(i[0])
		print "arg is " + str(i[1])
		if opt == "-b":
#reader = csv.reader(arg)
			blockDevs = arg.split(",")
			print "parsed blockDevs:" + str(blockDevs)
		elif opt == "-i":
			netDevs = arg.split(",")
			print "parsed netDevs:" + str(netDevs)
		elif opt == "-t":
			interval = float(arg)
			print "parsed inteval:" + str(interval)

	devList = []
	count = 0
	#TODO: clean this up
	if len(sys.argv) == 1: # TODO:print stderr correctly
		print "Error: need a device list on the command line"
	if not blockDevs and not netDevs:
		print "usage: " + sys.argv[0] + " [-i <comma-delimited net interface list>][-b <comma-delimited drive list>]"
		print "Example: " + sys.argv[0] + " -i eth0 -b sda,sda1,sda3,sdb,sdc"
		raise Exception ("bad args")

	# these two loops could probably be factored out with the new inheritance model
	# and building devList could be handled during arg parsing
	for dev in blockDevs:
		print "adding " + dev 
		devList.append(BlockDeviceStats(count, dev))
		count += 1
	
	for dev in netDevs:
		print "adding " + dev
		devList.append(NetDeviceStats(count,dev))
		count += 1

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

finally:
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()
