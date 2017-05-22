import pigpio
import time;
from pigpioFIFO import pigpioFIFO
from motor import Motor, Integrator, Command
from profiler import print_prof_data

motor = Motor(17)
integrator = Integrator(motor)

fifo = pigpioFIFO(2000, 0.1)
fifo.callBack = integrator.integrate

#Command(pos, vel)
integrator.g00(100)
integrator.g00(200)
integrator.g00(1000)
integrator.g00(10000)
integrator.g00(20000)

time.sleep(1)

while fifo.pi.wave_tx_at() != 9999:
    print_prof_data()
    time.sleep(1)

time.sleep(5)

fifo.pi.wave_tx_stop()
fifo.pi.stop()
