#pigpio makes it possible to send waves (series of pulses) to a gpio using DMA
#it also allows to start a wave after the previous one has finished. This is awesome.
#However, this process is manual. The user has to keep track of sent waves, wave IDs, not exceeding the maximum number of waves,
#and cleaning up after himself

#pigpioFIFO simplifies the usage of pigpio by exposing an unlimited fifo to the user
#the user just has to add pulses to the fifo, and pigpioFIFO manages everything else


import pigpio
import time, threading
from Queue import *
from profiler import *

class pigpioFIFO:
    WAVE_MODE_ONE_SHOT = 0
    WAVE_MODE_ONE_SHOT_SYNC = 2

    def __init__(self, pulsesPerPacket, timerPeriod):
        #Maximum number of pulses to send at once. Decreasing this number reduces lag but also requires faster checking and sending
        self.pulsesPerPacket = pulsesPerPacket
        #How often to check if we can send more pulses
        self.timerPeriod = timerPeriod

        #List where pulses are stored before being sent to pigpio
        #pulses are added using the "add" method
        self.pulseBuffer = []

        self.pi = pigpio.pi()
        self.pi.wave_clear()

        #Maximum number of pulses pigpio accepts in it's queue
        self.maxPulses = self.pi.wave_get_max_pulses() - 1000

        #Each chunk of pulses is given an ID by pigpio. In this list we store all the currently sent IDs that are waiting to be run
        self.runningWids = []
        #This list stores the length of each pulse chunk we've sent that hasn't run yet. We use it to make sure we don't exceed maxPulses
        self.runningPulses = []
        #Sum of all lengths in runningPulses
        self.totalPulsesInQueue = 0

        #self.cb3 = self.pi.callback(17)
        self.counter = 0;

        #print("Tally", self.cb3.tally())
        #Info
        print("Max Seconds", self.pi.wave_get_max_micros()/1000000)
        print("Max Pulses", self.pi.wave_get_max_pulses())

        self.callBack = None
        self.checkAndSend()

    #This method runs every timerPeriod. It checks if there are pulses waiting to be sent to pigpio (in pulseBuffer)
    #and wether there is enough space in pigpio
    @profile
    def checkAndSend(self):
        if self.callBack == None:
            threading.Timer(self.timerPeriod, self.checkAndSend).start()
            return
        #print("Pulse Counter", self.cb3.tally())

        availableSpace = self.maxPulses - self.totalPulsesInQueue

        while availableSpace > self.pulsesPerPacket:
            self.popUnusedWIDs()
            #We construct a new waveform (a series of pulses)
            wf = self.callBack(self.pulsesPerPacket / 2)

            #If the waveform is not empty, we send it to pigpio
            if wf != None and len(wf) > 0:
                self.addWaveToPigpio(wf)
                availableSpace = self.maxPulses - self.totalPulsesInQueue
            else:
                threading.Timer(self.timerPeriod, self.checkAndSend).start()
                return
        self.popUnusedWIDs()
        threading.Timer(self.timerPeriod, self.checkAndSend).start()


    @profile
    def addWaveToPigpio(self, wf):
        #Check the ID of the currently running wave
        current = self.pi.wave_tx_at()
        if(current == 9998 or current == 9999):
            mode = self.WAVE_MODE_ONE_SHOT
            print("UnderFlow!")
        else:
            #Try to synchronize the next wave with the previous wave
            mode = self.WAVE_MODE_ONE_SHOT_SYNC

        self.pi.wave_add_generic(wf)
        wid = self.pi.wave_create()

        self.pi.wave_send_using_mode(wid, mode)
        #Update our lists where we keep track of what we've sent
        self.runningWids.append(wid)
        self.runningPulses.append(len(wf))
        self.totalPulsesInQueue+=len(wf)

    @profile
    def popUnusedWIDs(self):
        #Clean up unused WIDs (Waves that have already run and can be cleared to make up space)
        #We check the currently running WID and delete every wave that came before it, because it must have already run
        while len(self.runningWids) > 0 and self.pi.wave_tx_at() != self.runningWids[0]:
            print("Clean", self.pi.wave_tx_at(), self.runningWids)
            self.pi.wave_delete(self.runningWids[0])
            self.totalPulsesInQueue-=self.runningPulses[0]
            self.runningPulses.pop(0)
            self.runningWids.pop(0)
