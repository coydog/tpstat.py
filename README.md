
tpstat.py
=========

#### Throughput monitor for Linux in Python using curses and procfs

This is a Linux throughput monitor in Python. It depends on the procfs module,
so you will need that in your python path:

  [python procfs](https://pypi.python.org/pypi/procfs/0.1.2 "python procfs")

This was originally designed to measure throughput on block devices (disks,
SSD's, etc), but I'm slowly hacking in support for network devices.

Accuracy and precision are still being worked on. The rate calculation should
depend on a timer, rather than assuming the only time that has elapsed is what
we spent in time.sleep(). We might get away with this in C but it's more
dubious in Python.

Released under the terms of the GNU General Public License, version 3.

Some features are still works in progress. This includes mount point lookup and
network device support.

Invoke it on the command line with -i and/or -b. Each of these options takes
a comma-delimited list of devices as an argument:
  `tpmon.py -b sda,sdc,sdb3,sdb2,sdb -i eth0,eth1`

This was written largely as an exercise to help me learn curses and Python OOP,
so it may be rough around the edges. Feel free to report bugs.

Ideas for future development:
-----------------------------

  * inheritance for the *Stats classes
  * look up all monitorable block devices and use those as defaults
  * time interval as a command-line arg
  * a more useful "Avg field, like a 5-second average
  * an animated scrolling graph in curses
  * command-line args -n -b for lists of block, net devices
