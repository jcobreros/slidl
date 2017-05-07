#pigpio makes it possible to send waves (series of pulses) to a gpio
#it also allows to start a wave after the previous one has finished
#however, this process is manual. The user has to keep track of sent waves, wave IDs, not exceeding the maximum number of waves, and cleaning up after himself

#pigpioFIFO simplifies the usage of pigpio by exposing a fifo to the user
#the user just has to add pulses to the fifo, and pigpioFIFO manages everything else


import pigpio
import time, threading

class pigpioFIFO:
    WAVE_MODE_ONE_SHOT = 0
    WAVE_MODE_ONE_SHOT_SYNC = 2

    def __init__(self, pulsesPerPacket, timerPeriod):
        self.pulsesPerPacket = pulsesPerPacket
        self.timerPeriod = timerPeriod
        self.pulseDuration = 200

        self.pulseBuffer = []

        self.pi = pigpio.pi()
        self.pi.wave_clear()

        self.maxPulses = self.pi.wave_get_max_pulses()

        self.runningWids = []
        self.runningPulses = []
        self.totalPulsesInQueue = 0

        self.cb3 = self.pi.callback(17)
        self.counter = 0;

        print("Tally", self.cb3.tally())
        #Info
        print("Max Seconds", self.pi.wave_get_max_micros()/1000000)
        print("Max Pulses", self.pi.wave_get_max_pulses())

        self.checkAndSend()

    def add(self, pulses):
        for p in pulses:
            self.pulseBuffer.append(p)

    def checkAndSend(self):
        print("Pulse Counter", self.cb3.tally())
        availableSpace = self.maxPulses - self.totalPulsesInQueue
        #print("Available",availableSpace)
        while availableSpace > 0 and len(self.pulseBuffer) > 0:
            wf = []
            numPulsesToRequest = min( self.pulsesPerPacket, len(self.pulseBuffer) )
            for x in range(0, numPulsesToRequest):
                thisPulse = self.pulseBuffer.pop(0)
                wf.append(pigpio.pulse(1<<17, 0, self.pulseDuration))
                wf.append(pigpio.pulse(0, 1<<17, thisPulse.t - self.pulseDuration))

            if len(wf) > 0:
                self.addWaveToPigpio(wf)
                availableSpace = self.maxPulses - self.totalPulsesInQueue

        self.popUnusedWIDs()
        threading.Timer(self.timerPeriod, self.checkAndSend).start()

    def addWaveToPigpio(self, wf):
        current = self.pi.wave_tx_at()
        if(current == 9998 or current == 9999):
            mode = self.WAVE_MODE_ONE_SHOT
            print(current)
        else:
            mode = self.WAVE_MODE_ONE_SHOT_SYNC
        
        self.pi.wave_add_generic(wf)
        wid = self.pi.wave_create()

        self.pi.wave_send_using_mode(wid, mode)
        self.runningWids.append(wid)
        self.runningPulses.append(len(wf))
        self.totalPulsesInQueue+=len(wf)

    def popUnusedWIDs(self):
        #Clean up unused WIDs
        while len(self.runningWids) > 0 and self.pi.wave_tx_at() != self.runningWids[0]:
            #print("Clean", self.pi.wave_tx_at(), self.runningWids)
            self.pi.wave_delete(self.runningWids[0])
            self.totalPulsesInQueue-=self.runningPulses[0]
            self.runningPulses.pop(0)
            self.runningWids.pop(0)
