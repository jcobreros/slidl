import pigpio
import math
import time

class Motor:
    def __init__(self, gpio):
        self.gpio = gpio
        self.position = 0       #steps
        self.velocity = 0       #steps/s
        self.acceleration = 2000.0  #steps/s2
        self.maxVelocity = 4000.0   #steps/s

        pigpio.pi().set_mode(self.gpio, pigpio.OUTPUT)


class Integrator:
    def __init__(self, motor):
        self.motor = motor
        self.pulseDuration = 200

    def integrate(self, pos):
        print("New Movement to", pos)
        #Get ramp up, steady and ramp down segments
        commands = self.calculateTrapezoidalProfile(pos - self.motor.position, 0, 0)
        #array where we store pulses to send
        pulseBuffer = []
        totalTime = 0
        #f = open('motor.csv', 'w')
        for c in commands:
            #We calculate nextTime in an iterative way
            if(c.acceleration >= 0):
                #Accelerating: Steps go from 0 to N
                accelStepNumber = 0
                accelStepDir = 1
            else:
                #Decelerating: Steps go from N to 0
                accelStepNumber = c.position - 1
                accelStepDir = -1
            #nextTime for step 0
            c0 = math.sqrt(2/self.motor.acceleration)


            print ("Command","Pos", c.position,"Acc", c.acceleration)
            targetPosition = self.motor.position + c.position

            while targetPosition - self.motor.position > 0:
                if(c.acceleration != 0):
                    nextTime = c0 * ( math.sqrt(accelStepNumber + 1) - math.sqrt(accelStepNumber) )
                    self.motor.velocity = 1 / nextTime
                    accelStepNumber+=accelStepDir
                else:
                    if(self.motor.velocity == 0):
                        #if not accelerating and speed = 0, we can't move!
                        return
                    nextTime = 1 / self.motor.velocity

                self.motor.position += 1

                totalTime+=nextTime
                #print("Next",nextTime,"V", self.motor.velocity,"P", self.motor.position)
                #csvLine = (str(totalTime) + ";" + str(self.motor.velocity) +"\n").replace('.', ',')
                #f.write(csvLine)  # python will convert \n to os.linesep

                nextTime = math.floor(nextTime * 1000000)
                pulseBuffer.append(pigpio.pulse(1<<self.motor.gpio, 0, self.pulseDuration))
                pulseBuffer.append(pigpio.pulse(0, 1<<self.motor.gpio, nextTime - self.pulseDuration))

        print "Done"
        #f.close()  # you can omit in most cases as the destructor will call it
        return pulseBuffer

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
            commands.append(Command(distanceToMaxSpeed/2, self.motor.acceleration))
            commands.append(Command(distanceToMaxSpeed/2, -self.motor.acceleration))
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

class Pulse:
    def __init__(self, d, t):
        self.direction = d
        self.t = t
