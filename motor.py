import pigpio
import math
import time
from profiler import profile

class Motor:
    def __init__(self, gpio):
        self.gpio = gpio
        self.position = 0       #steps
        self.velocity = 0       #steps/s
        self.acceleration = 12000.0  #steps/s2
        self.maxVelocity = 6000.0   #steps/s

        pigpio.pi().set_mode(self.gpio, pigpio.OUTPUT)


class Integrator:
    def __init__(self, motor):
        self.motor = motor
        self.pulseDuration = 100
        self.commandQueue = []
        self.currentCommandStep = 0
        self.lastCommand = {"pos" : 0, "vel": 0, "acc": 0}
        self.pulseBuffer = []
        self.pulseBufferLoopable = False

    def g00(self, pos):
        print("New Movement to", pos)
        #Get ramp up, steady and ramp down segments
        self.commandQueue.extend(self.calculateTrapezoidalProfile(pos - self.motor.position, 0, 0))

    @profile
    def integrate(self, steps = -1):
        if len(self.commandQueue) == 0:
            return []
        #array where we store pulses to send

        if steps < self.commandQueue[0].position - self.currentCommandStep:
            if self.pulseBufferLoopable and self.commandQueue[0].acceleration == 0:
                print("Reusing pulseBuffer")
                self.currentCommandStep+=steps
                return self.pulseBuffer
        #If we didn't reuse the last pulseBuffer, let's see if we can reuse the next one
        self.pulseBufferLoopable = True

        self.pulseBuffer = []
        while steps > 0 and len(self.commandQueue) > 0:
            #print ("Command","Pos", self.commandQueue[0].position,"Acc", self.commandQueue[0].acceleration, self.currentCommandStep)
            stepsForCommand = int(min(steps, self.commandQueue[0].position - self.currentCommandStep))
            if(stepsForCommand > 0):
                steps -= stepsForCommand
                self.integrateSteps(stepsForCommand , self.pulseBuffer)

            if(stepsForCommand == 0):
                #We changed commands during this pulseBuffer, so it's not loopable
                self.pulseBufferLoopable = False

                self.currentCommandStep = 0
                self.commandQueue.pop(0)
                if len(self.commandQueue) == 0:
                    return self.pulseBuffer
                self.lastCommand["pos"] = self.commandQueue[0].position
                self.lastCommand["acc"] = self.commandQueue[0].acceleration
        #f = open('motor.csv', 'w')
        #f.close()  # you can omit in most cases as the destructor will call it
        return self.pulseBuffer
    @profile
    def integrateSteps(self, steps, pulseBuffer):
        #We calculate nextTime in an iterative way
        #nextTime for step 0
        print("Integrating", steps)
        c0 = math.sqrt(2/self.motor.acceleration)

        for s in xrange(int(steps)):
            if(self.commandQueue[0].acceleration != 0):
                if(self.commandQueue[0].acceleration >= 0):
                    accelFactor = self.currentCommandStep
                else:
                    accelFactor = self.commandQueue[0].position - self.currentCommandStep

                nextTime = c0 * ( math.sqrt(accelFactor + 1) - math.sqrt(accelFactor) )
                self.motor.velocity = 1 / nextTime
            else:
                if(self.motor.velocity == 0):
                    #if not accelerating and speed = 0, we can't move!
                    return pulseBuffer
                nextTime = 1 / self.motor.velocity

            self.motor.position += 1
            self.currentCommandStep+= 1

            #print("Next",nextTime,"V", self.motor.velocity,"P", self.motor.position)
            #csvLine = (str(totalTime) + ";" + str(self.motor.velocity) +"\n").replace('.', ',')
            #f.write(csvLine)  # python will convert \n to os.linesep

            nextTime = math.floor(nextTime * 1000000)
            pulseBuffer.append(pigpio.pulse(1<<self.motor.gpio, 0, self.pulseDuration))
            pulseBuffer.append(pigpio.pulse(0, 1<<self.motor.gpio, nextTime - self.pulseDuration))

    def calculateTrapezoidalProfile(self, deltaPos, vIni, vEnd):
        commands = []
        #This method takes a motion command and splits it into two or three commands
        #for trapezoidal or triangular speed profile

        #v' = v + a*t --> t = (v' - v) / a
        timeToMaxSpeed = (self.motor.maxVelocity - vIni) / self.motor.acceleration
        print("Time to Max Speed", timeToMaxSpeed)

        distanceToMaxSpeed = vIni * timeToMaxSpeed + 0.5 * self.motor.acceleration * math.pow(timeToMaxSpeed, 2)
        print("Distance to Max Speed", distanceToMaxSpeed)

        if distanceToMaxSpeed >= (deltaPos / 2):
            #Triangular profile
            commands.append(Command(deltaPos/2, self.motor.acceleration))
            commands.append(Command(deltaPos/2, -self.motor.acceleration))
        else:
            #Trapezoidal profile
            commands.append(Command(distanceToMaxSpeed, self.motor.acceleration))
            commands.append(Command(deltaPos - 2*distanceToMaxSpeed, 0))
            commands.append(Command(distanceToMaxSpeed, -self.motor.acceleration))
        return commands


class Command:
    def __init__(self, p, a):
        self.position = p
        self.acceleration = a
