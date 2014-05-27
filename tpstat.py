#!/usr/bin/python2
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
	def __init__(self):
		val = 0;
		lastVal = 0
		delta = 0
		avg = 0
		peak = 0
		total = 0
		

class DeviceStats(object):
	"parent class for different device types" 
	def __init__(self, position, dev):
		if type(self) == DeviceStats:
			raise Exception ("DeviceStats is an abstract class")
		self.lines = 6 # should be overrideable
		self.position = position
		self.dev = dev

		self.readTracker = StatTracker()

		self.readTracker.count = 0
		self.fetch(dev) # TODO: inheritance. if I call this here in super's init
					 # will it call the child method?
		#TODO: encapsulate, add write stats
		self.readTracker.lastVal = self.readTracker.val
		self.readTracker.delta = 0
		self.readTracker.avg = 0
		self.readTracker.peak = 0
		self.readTracker.total = 0

	def fetch(self, dev):
		"virtual method to fetch device-specific stats from procfs"
		pass

	def calculate (self):
		self.readTracker.count += 1
		self.fetch(self.dev)
		self.readTracker.delta = self.readTracker.val - self.readTracker.lastVal
		self.readTracker.total += self.readTracker.delta
		self.readTracker.avg = self.readTracker.total / self.readTracker.count
		if self.readTracker.delta > self.readTracker.peak:
			self.readTracker.peak = self.readTracker.delta
		self.readTracker.lastVal = self.readTracker.val


class NetDeviceStats(DeviceStats):
	"per-interface statistics and display methods"
	def __init__(self, position, dev):
		super(NetDeviceStats, self).__init__(position, dev)

	def fetch(self, dev):
		# needs dev as an arg to avoid circular dependencies in
		# parent and subclass ctors
		"fetch net device stat value from procfs"
		self.readTracker.val = proc.net.dev[dev].receive.bytes
		#self.writeTracker.val = proc.net.dev[dev].transmit.bytes
	
	def printStats (self):
		startLine = self.position * self.lines
		stdscr.addstr(startLine, 0, "interface " + self.dev + "\t ")
		stdscr.addstr(startLine+1, 0, "Cur:\t" + formatReadableRate(self.readTracker.delta))
		stdscr.addstr(startLine+2, 0, "\t" + formatReadableRate(self.readTracker.delta, True))
		stdscr.addstr(startLine+3, 0, "Avg:\t" + formatReadableRate(self.readTracker.avg))
		stdscr.addstr(startLine+4, 0, "Peak:\t" + formatReadableRate(self.readTracker.peak))
		stdscr.addstr(startLine+5, 0, "Total:\t" + formatReadableAbs(self.readTracker.total))

class BlockDeviceStats(DeviceStats):
	"per-device statistics and methods for displaying them"

	def __init__(self, position, dev):
		self.sectorSize = statvfs("/dev/" + dev).f_bsize
		super(BlockDeviceStats, self).__init__(position, dev)
		self.mounts = ""
		#self.mounts = getMounts(self.dev)

	def fetch(self, dev):
		"fetch block dev stats from procfs"
		self.readTracker.val = proc.diskstats[dev].read.sectors * self.sectorSize
		#self.writeTracker.val = proc.diskstats[dev].write.sectors * self.sectorSize

	def printStats (self):
		startLine = self.position * self.lines
		stdscr.addstr(startLine, 0, "/dev/" + self.dev + "\t" + " " + str(self.mounts));
		stdscr.addstr(startLine+1, 0, "Cur:\t" + formatReadableRate(self.readTracker.delta))
		stdscr.addstr(startLine+2, 0, "Avg:\t" + formatReadableRate(self.readTracker.avg))
		stdscr.addstr(startLine+3, 0, "Peak:\t" + formatReadableRate(self.readTracker.peak))
		stdscr.addstr(startLine+4, 0, "Total:\t" + formatReadableAbs(self.readTracker.total))
		

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
