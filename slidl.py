import pigpio
import time;
from pigpioFIFO import pigpioFIFO
from motor import Motor, Integrator, Command

motor = Motor(17)
integrator = Integrator(motor)


fifo = pigpioFIFO(1000, 0.1)
#Command(pos, vel)
pulses = integrator.integrate(32000)
print("Total pulses generated", len(pulses))
fifo.add(pulses)

time.sleep(1)

while fifo.pi.wave_tx_at() != 9999:
    time.sleep(1)

time.sleep(10)

fifo.pi.wave_tx_stop()
fifo.pi.stop()
