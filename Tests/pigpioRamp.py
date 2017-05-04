import pigpio
import time

try:
  pi = pigpio.pi()
  GPIO_pin=4

  pi.set_mode(GPIO_pin, pigpio.OUTPUT)
  pi = pigpio.pi() # connect to local Pi

  freq = 30000 # Hz

  period = 1.0 / freq * 10**6

  print "period: %f" % period


  ramp_time = 1 # sec

  start_date = time.time()

  for i in range(1000):

    time_diff =  time.time() - start_date

    ramp_loc = time_diff / ramp_time
    #c = (i % 2) + 1
    if ramp_loc >= 1.0:
      break

    print "ramp location: ", ramp_loc

    if ramp_loc <= .001:
      ramp_loc = .001

    c = ramp_loc

    square = []
    #                          ON       OFF    MICROS
    square.append(pigpio.pulse(1<<GPIO_pin, 0,       period/2/c))
    square.append(pigpio.pulse(0,       1<<GPIO_pin, period/2/c))



    #pi.wave_clear()
    pi.wave_add_generic(square)

    wid = pi.wave_create()

    if wid >= 0:
      pi.wave_send_repeat(wid)

  time.sleep(5)

finally:
  pi.wave_clear()
  pi.wave_tx_stop() # <- important!
  pi.stop()
