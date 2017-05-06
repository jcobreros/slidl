import pigpio
import time;
from pigpioFIFO import pigpioFIFO
from motor import Motor, Integrator, Command

motor = Motor(17)
integrator = Integrator(motor)

fifo = pigpioFIFO(100, 0.2)

time.sleep(1)
#Command(pos, vel)
cmd = Command(96, 50)
pulses = integrator.integrate(cmd)
for p in pulses:
    fifo.pulseBuffer.append(p)

cmd = Command(192, 100)
pulses = integrator.integrate(cmd)
for p in pulses:
    fifo.pulseBuffer.append(p)

cmd = Command(384, 200)
pulses = integrator.integrate(cmd)
for p in pulses:
    fifo.pulseBuffer.append(p)

time.sleep(1)

while fifo.pi.wave_tx_at() != 9999:
    time.sleep(0.2)

time.sleep(1)

fifo.pi.wave_tx_stop()
fifo.pi.stop()
