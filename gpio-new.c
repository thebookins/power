/*
 * This file was adapted and simplified from the example isr.c
 * distributed with wiringPi by Gordon Henderson
 *
 * It waits for an interrupt on GPIO 1 and prints 'Interrupt' to stdout
 * It is used with a python script to monitor pulses from a power meter
 * and report the usage to EmonCMS
 *
 * See here: http://github.com/kieranc/power/
 *
 * Copyright (c) 2013 Gordon Henderson.
 ***********************************************************************
 * This file is part of wiringPi:
 *	https://projects.drogon.net/raspberry-pi/wiringpi/
 *
 *    wiringPi is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Lesser General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    wiringPi is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public License
 *    along with wiringPi.  If not, see <http://www.gnu.org/licenses/>.
 ***********************************************************************
 */


#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>
#include <limits.h>
#include <wiringPi.h>

#define	DEBOUNCE_TIME	360

// int busy = 0;
int debounceTime = 0 ;

void myInterrupt() {
    if (millis () < debounceTime)
    {
        return ;
    }
    // if (busy) return;
    // busy = 1;
    printf ("Interrupt\n") ;
    fflush (stdout) ;
    debounceTime = millis () + DEBOUNCE_TIME ;
    // usleep(360000); // ignore multiple pulses within a 360 ms window (limits power reported to 10 kW)
    // busy = 0;
}

/*
 *********************************************************************************
 * main
 *********************************************************************************
 */

int main (void)
{
    wiringPiSetup () ;

    wiringPiISR (1, INT_EDGE_FALLING, &myInterrupt) ;

    for (;;) {
        sleep(UINT_MAX);
//        sleep(0.036);
//        myInterrupt();
    }
    return 0;
}
