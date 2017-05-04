#!/usr/bin/env python

import time
import pigpio

WAVES=5
GPIO=17

wid=[0]*WAVES

pi = pigpio.pi() # Connect to local Pi.

pi.set_mode(GPIO, pigpio.OUTPUT);

for i in range(WAVES):
   pi.wave_add_generic([
      pigpio.pulse(1<<GPIO, 0, 1000),
      pigpio.pulse(0, 1<<GPIO, (i+1)*1000)]);
   pi.wave_add_generic([
      pigpio.pulse(1<<GPIO, 0, 1000),
      pigpio.pulse(0, 1<<GPIO, (i+1)*1000)]);  

   wid[i] = pi.wave_create();

pi.wave_chain([
   wid[4], wid[3], wid[2],       # transmit waves 4+3+2
   255, 0,                       # loop start
      wid[0], wid[0], wid[0],    # transmit waves 0+0+0
      255, 0,                    # loop start
         wid[0], wid[1],         # transmit waves 0+1
         255, 2, 0x88, 0x13,     # delay 5000us
      255, 1, 30, 0,             # loop end (repeat 30 times)
      255, 0,                    # loop start
         wid[2], wid[3], wid[0], # transmit waves 2+3+0
         wid[3], wid[1], wid[2], # transmit waves 3+1+2
      255, 1, 10, 0,             # loop end (repeat 10 times)
   255, 1, 5, 0,                 # loop end (repeat 5 times)
   wid[4], wid[4], wid[4],       # transmit waves 4+4+4
   255, 2, 0x20, 0x4E,           # delay 20000us
   wid[0], wid[0], wid[0],       # transmit waves 0+0+0
   ])

while pi.wave_tx_busy():
   current = pi.wave_tx_at()
   if(current==9998): print("Not found")
   else: print(current)
   time.sleep(0.1);

for i in range(WAVES):
   pi.wave_delete(wid[i])

pi.stop()
