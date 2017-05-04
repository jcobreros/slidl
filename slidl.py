import pigpio
import time;
from pulseDriver import PulseDriver
from motor import Motor, Integrator, Command

motor = Motor(17)
integrator = Integrator(motor)
pd = PulseDriver(integrator)

time.sleep(1)
#Command(pos, vel)
cmd = Command(96, 50)
integrator.integrate(cmd)
cmd = Command(192, 100)
integrator.integrate(cmd)
cmd = Command(384, 200)
integrator.integrate(cmd)

time.sleep(1)

while pd.pi.wave_tx_at() != 9999:
    time.sleep(0.2)

time.sleep(1)
pd.pi.wave_tx_stop()
pd.pi.stop()
