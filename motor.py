import pigpio
import math

class Motor:
    def __init__(self, gpio):
        self.gpio = gpio
        self.position = 0       #steps
        self.velocity = 0       #steps/s
        self.acceleration = 100.0  #steps/s2
        self.maxVelocity = 200.0   #steps/s

        pigpio.pi().set_mode(self.gpio, pigpio.OUTPUT)


class Integrator:
    def __init__(self, motor):
        self.motor = motor
        self.pulseDuration = 1000

    def integrate(self, pos):
        file = open("times.csv", "w")
        commands = self.calculateTrapezoidalProfile(pos - self.motor.position, 0, 0)
        pulseBuffer = []
        for c in commands:
            print (c.position, c.acceleration)
            targetPosition = self.motor.position + c.position
            while targetPosition - self.motor.position > 0:
                if(c.acceleration != 0):
                    discriminant = math.pow(self.motor.velocity, 2) + (4 * c.acceleration)
                    file.write(str(discriminant) + ";" + str(self.motor.velocity) + ";\r\n")

                    if discriminant < 0:
                        print("Zero!", discriminant)
                        discriminant = 0
                    nextTime = (- self.motor.velocity + math.sqrt(discriminant) ) / (2 * c.acceleration)
                    #print(nextTime, nextTime2, self.motor.velocity)

                    self.motor.velocity += c.acceleration * nextTime

                else:
                    if(self.motor.velocity == 0):
                        return
                    #self.motor.velocity = self.motor.maxVelocity
                    print("Vel", self.motor.velocity)
                    nextTime = 1 / self.motor.velocity

                self.motor.position += self.motor.velocity * nextTime

                #print("V", self.motor.velocity, "term", term, "NextTime", nextTime)

                nextTime = math.floor(nextTime * 1000000)
                #file.write(str(int(nextTime)) + "\r\n")

                if (nextTime < 10):
                    print nextTime
                pulseBuffer.append(pigpio.pulse(1<<self.motor.gpio, 0, self.pulseDuration))
                pulseBuffer.append(pigpio.pulse(0, 1<<self.motor.gpio, nextTime - self.pulseDuration))
        print "Done"
        return pulseBuffer

    def calculateTrapezoidalProfile(self, deltaPos, vIni, vEnd):
        commands = []
        #This method takes a motion command and splits it into two or three commands
        #for trapezoidal or triangular speed profile

        #v' = v + a*t --> t = (v' - v) / a
        timeToMaxSpeed = (self.motor.maxVelocity - vIni) / self.motor.acceleration
        print("t2s", timeToMaxSpeed)
        #p' = p + v*t + a*t^2
        distanceToMaxSpeed = round(vIni * timeToMaxSpeed + 0.5 * self.motor.acceleration * math.pow(timeToMaxSpeed, 2))
        print("d2s", distanceToMaxSpeed)
        if distanceToMaxSpeed >= (deltaPos / 2):
            triangularShape = True
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
