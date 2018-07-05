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

pulsecount = 0

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

# This function sends the instantaneous power to EmonCMS (called every 10 seconds below)
def SendPulses():
    global pulsecount

    # Calculate ideal solar output for a 3kW system in Sydney (+10 hours), for simulation purposes in EmonCMS
    # remove if not needed
    solarnow = datetime.utcnow() + timedelta(hours=10)
    seconds_since_midday = (solarnow - solarnow.replace(hour=12, minute=0, second=0, microsecond=0)).total_seconds()
    theta = (math.pi / 2) * seconds_since_midday / (6 * 3600)

    solar = 3000 * math.cos(theta)
    solar = max(solar,0)

    #	print ("Pulses: %i") % pulsecount # Uncomment for debugging.
    # The next line calculates a power value in watts from the number of pulses, my meter is 1000 pulses per kWh, you'll need to modify this if yours is different.
    power = pulsecount * 10
    #	print ("Power: %iW") % power # Uncomment for debugging.
    pulsecount = 0;

    path = ('/input/post?node=emontx&fulljson={"power":%0.1f,"solar":%0.1f}&apikey=<insert API key here>') % (power, solar) # You'll need to put in your API key here from EmonCMS
    connection = httplib.HTTPConnection("emoncms.org")
    connection.request("GET", path)
    res = connection.getresponse()
    # TODO: deal with a bad response

# Start the scheduler
sched = BackgroundScheduler()
sched.add_job(SendPulses, 'interval', seconds=10)
sched.start()

# lasttime = time.time()*1000
for line in runProcess(["/usr/local/bin/gpio-new"]): # GPIO pin 7 on the Pi
    pulsecount += 1
