import pigpio

class Motor:
    def __init__(self, gpio):
        self.gpio = gpio
        self.position = 0

class Integrator:
    def __init__(self, motor):
        self.motor = motor
        self.pulseBuffer = []

    def integrate(self, command):

        if command.velocity == 0:
            return
        deltaPos = command.position - self.motor.position
        microsBetweenPulses = 1000000 / command.velocity
        for x in range(0, abs(deltaPos)):
            self.pulseBuffer.append(Pulse(1, microsBetweenPulses))

class Command:
    def __init__(self, p, v):
        self.position = p
        self.velocity = v

class Pulse:
    def __init__(self, d, t):
        self.direction = d
        self.t = t
