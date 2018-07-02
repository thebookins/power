#!/usr/bin/python

"""
	Modified by KieranC to submit pulse count to Open Energy Monitor EmonCMS API

	Modified by thebookins to run with Python 3.1.0, output instantaneous power
	every 10 seconds, and simulate solar output

	Power Monitor
	Logs power consumption to an SQLite database, based on the number
	of pulses of a light on an electricity meter.

	Copyright (c) 2012 Edward O'Regan

	Permission is hereby granted, free of charge, to any person obtaining a copy of
	this software and associated documentation files (the "Software"), to deal in
	the Software without restriction, including without limitation the rights to
	use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
	of the Software, and to permit persons to whom the Software is furnished to do
	so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.
"""

import time, os, subprocess, httplib,  math
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# The next 2 lines enable logging for the scheduler. Uncomment for debugging.
#import logging
#logging.basicConfig()

power=0
lasttime=0


# This function monitors the output from gpio-irq C app
# Code from vartec @ http://stackoverflow.com/questions/4760215/running-shell-command-from-python-and-capturing-the-output
def runProcess(exe):
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
      retcode = p.poll() #returns None while subprocess is running
      line = p.stdout.readline()
      yield line
      if(retcode is not None):
        break


# This function converts an interval between pulses (in seconds) to an instantaneous power reading (in Watts)
# For a meter that outputs 1000 pulses per kWh (modify if different)
def intervalToPower(interval):
	return 3600 / interval

# This function sends the instantaneous power to EmonCMS (called every 10 seconds below)
def SendPulses():
	global power

	# Calculate ideal solar output for a 3kW system in Sydney (+10 hours), for simulation purposes in EmonCMS
	# remove if not needed
        solarnow = datetime.utcnow() + timedelta(hours=10)
	seconds_since_midday = (solarnow - solarnow.replace(hour=12, minute=0, second=0, microsecond=0)).total_seconds()
	theta = (math.pi / 2) * seconds_since_midday / (6 * 3600)

	solar = 3000 * math.cos(theta)
	solar = max(solar,0)

	# Calculate the power if an impulse had arrived now; if this is less than power, reduce power to this value
	# as we know the power cannot be greater
	provisionalPower = intervalToPower((time.time()*1000 - lasttime) / 1000)
	if(provisionalPower < power):
	  power = provisionalPower

#	print ("Power: %iW) % power # Uncomment for debugging.
        url = ("/emoncms/input/post?node=1&json={power:%0.1f,solar:%0.1f}&apikey=<insert API key here>") % (power, solar) # You'll need to put in your API key here from EmonCMS
        connection = httplib.HTTPConnection("localhost")
        connection.request("GET", url)

# Start the scheduler
sched = BackgroundScheduler()
sched.add_job(SendPulses, 'interval', seconds=10)
sched.start()

lasttime = time.time()*1000
for line in runProcess(["/usr/local/bin/gpio-new"]): # GPIO pin 7 on the Pi
    timenow = time.time()*1000
    if(timenow >= lasttime + 360): # ignore multiple pulses within a 360 ms window (limits power reported to 10 kW)
      period_in_seconds = (timenow - lasttime) / 1000
      power = intervalToPower(period_in_seconds)
      lasttime = timenow
