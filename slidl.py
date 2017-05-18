import pigpio
import time;
from pigpioFIFO import pigpioFIFO
from motor import Motor, Integrator, Command

motor = Motor(17)
integrator = Integrator(motor)

fifo = pigpioFIFO(200, 0.2)

time.sleep(1)
#Command(pos, vel)
pulses = integrator.integrate(1600)
fifo.add(pulses)

time.sleep(1)

while fifo.pi.wave_tx_at() != 9999:
    time.sleep(0.2)

time.sleep(1)

fifo.pi.wave_tx_stop()
fifo.pi.stop()
