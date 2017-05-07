#pigpio makes it possible to send waves (series of pulses) to a gpio
#it also allows to start a wave after the previous one has finished
#however, this process is manual. The user has to keep track of sent waves, wave IDs, not exceeding the maximum number of waves, and cleaning up after himself

#pigpioFIFO simplifies the usage of pigpio by exposing an unlimited fifo to the user
#the user just has to add pulses to the fifo, and pigpioFIFO manages everything else


import pigpio
import time, threading
from Queue import *

class pigpioFIFO:
    WAVE_MODE_ONE_SHOT = 0
    WAVE_MODE_ONE_SHOT_SYNC = 2

    def __init__(self, pulsesPerPacket, timerPeriod):
        #Maximum number of pulses to send at once. Decreasing this number reduces lag but also requires faster checking and sending
        self.pulsesPerPacket = pulsesPerPacket
        #How often to check if we can send more pulses
        self.timerPeriod = timerPeriod
        self.pulseDuration = 200

        #List where pulses are stored before being sent to pigpio
        #pulses are added using the "add" method
        self.pulseBuffer = Queue()

        self.pi = pigpio.pi()
        self.pi.wave_clear()

        #Laximum number of pulses pigpio accepts in it's queue
        self.maxPulses = self.pi.wave_get_max_pulses()

        #Each chunk of pulses is given an ID by pigpio. In this list we store all the currently sent IDs that are waiting to be run
        self.runningWids = []
        #This list stores the length of each pulse chunk we've sent that hasn't run yet. We use it to make sure we don't exceed maxPulses
        self.runningPulses = []
        #Sum of all lengths in runningPulses
        self.totalPulsesInQueue = 0

        self.cb3 = self.pi.callback(17)
        self.counter = 0;

        print("Tally", self.cb3.tally())
        #Info
        print("Max Seconds", self.pi.wave_get_max_micros()/1000000)
        print("Max Pulses", self.pi.wave_get_max_pulses())

        self.checkAndSend()

    #Public method to add pulses to the pulseBuffer fifo
    def add(self, pulses):
        for p in pulses:
            self.pulseBuffer.put(p)

    #This method runs every timerPeriod. It checks if there are pulses waiting to be sent to pigpio (in pulseBuffer)
    #and wether there is enough space in pigpio
    def checkAndSend(self):
        print("Pulse Counter", self.cb3.tally())
        availableSpace = self.maxPulses - self.totalPulsesInQueue
        #print("Available",availableSpace)
        while availableSpace > 0 and not self.pulseBuffer.empty():
            #We construct a new waveform (a series of pulses)
            wf = []
            numPulsesToSend = min( self.pulsesPerPacket, self.pulseBuffer.qsize() )
            for x in range(0, numPulsesToSend):
                wf.append(self.pulseBuffer.get())

            #If the waveform is not empty, we send it to pigpio
            if len(wf) > 0:
                self.addWaveToPigpio(wf)
                availableSpace = self.maxPulses - self.totalPulsesInQueue

        self.popUnusedWIDs()
        threading.Timer(self.timerPeriod, self.checkAndSend).start()

    def addWaveToPigpio(self, wf):
        #Check the ID of the currently running wave
        current = self.pi.wave_tx_at()
        if(current == 9998 or current == 9999):
            mode = self.WAVE_MODE_ONE_SHOT
            print(current)
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

    def popUnusedWIDs(self):
        #Clean up unused WIDs (Waves that have already run and can be cleared to make up space)
        #We check the currently running WID and delete every wave that came before it, because it must have already run
        while len(self.runningWids) > 0 and self.pi.wave_tx_at() != self.runningWids[0]:
            #print("Clean", self.pi.wave_tx_at(), self.runningWids)
            self.pi.wave_delete(self.runningWids[0])
            self.totalPulsesInQueue-=self.runningPulses[0]
            self.runningPulses.pop(0)
            self.runningWids.pop(0)
