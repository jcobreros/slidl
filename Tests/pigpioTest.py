import pigpio
import time;

WAVE_MODE_ONE_SHOT = 0
WAVE_MODE_REPEAT = 1
WAVE_MODE_ONE_SHOT_SYNC = 2
WAVE_MODE_REPEAT_SYNC = 3

GPIO=17

pi = pigpio.pi()
pi.set_mode(GPIO, pigpio.OUTPUT)

#Info
print("CBS", pi.wave_get_cbs())
print("Max CBS", pi.wave_get_max_cbs())
print("Max Micros", pi.wave_get_max_micros())
print("Max Seconds", pi.wave_get_max_micros()/1000000)
print("Max Pulses", pi.wave_get_max_pulses())

#Clear all waveforms added by Wave_add_*
pi.wave_clear()

#1Sec 1KHz @ 50% duty
wf=[]
for x in range(0, 100):
    #pigpio.pulse(GPIO to turn ON, GPIO to turn OFF, delay in uS)
    wf.append(pigpio.pulse(1<<GPIO, 0,       500))
    wf.append(pigpio.pulse(0,       1<<GPIO, 500))
pi.wave_add_generic(wf)
wid0 = pi.wave_create()

#1Sec 1KHz @ 25% duty
wf2=[]
for x in range(0, 100):
    #pigpio.pulse(GPIO to turn ON, GPIO to turn OFF, delay in uS)
    wf2.append(pigpio.pulse(1<<GPIO, 0,       250))
    wf2.append(pigpio.pulse(0,       1<<GPIO, 750))
pi.wave_add_generic(wf2)
wid1 = pi.wave_create()

pi.wave_send_using_mode(wid0, WAVE_MODE_REPEAT)
time.sleep(5)
pi.wave_send_using_mode(wid1, WAVE_MODE_REPEAT)
#These two don run. Are waves deleted after they are created?
time.sleep(5)
pi.wave_send_using_mode(wid0, WAVE_MODE_ONE_SHOT_SYNC)
pi.wave_send_using_mode(wid1, WAVE_MODE_ONE_SHOT_SYNC)
time.sleep(2)

pi.wave_tx_stop()
pi.stop()
