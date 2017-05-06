import pigpio
import time, threading

class pigpioFIFO:
    WAVE_MODE_ONE_SHOT = 0
    WAVE_MODE_REPEAT = 1
    WAVE_MODE_ONE_SHOT_SYNC = 2
    WAVE_MODE_REPEAT_SYNC = 3

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

        self.timerCallback()


    def addWave(self, wf):

        mode = self.WAVE_MODE_ONE_SHOT_SYNC
        current = self.pi.wave_tx_at()
        if(current == 9998 or current == 9999):
            mode = self.WAVE_MODE_ONE_SHOT
            print(current)

        self.pi.wave_add_generic(wf)
        wid = self.pi.wave_create()

        self.pi.wave_send_using_mode(wid, mode)
        self.runningWids.append(wid)
        self.runningPulses.append(len(wf))
        self.totalPulsesInQueue+=len(wf)

        #print(self.pi.wave_tx_at(), self.runningWids, self.totalPulsesInQueue)

    def timerCallback(self):
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
                self.addWave(wf)
                availableSpace = self.maxPulses - self.totalPulsesInQueue

        self.popUnusedWIDs()
        threading.Timer(self.timerPeriod, self.timerCallback).start()

    def popUnusedWIDs(self):
        #Clean up unused WIDs
        while len(self.runningWids) > 0 and self.pi.wave_tx_at() != self.runningWids[0]:
            #print("Clean", self.pi.wave_tx_at(), self.runningWids)
            self.pi.wave_delete(self.runningWids[0])
            self.totalPulsesInQueue-=self.runningPulses[0]
            self.runningPulses.pop(0)
            self.runningWids.pop(0)
