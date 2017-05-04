print "Hello hostia 2"

from RPIO import PWM

# Setup PWM and DMA channel 0
PWM.setup(1, 0)
PWM.init_channel(0, 4000)

# Add some pulses to the subcycle
PWM.add_channel_pulse(0, 17, 0, 500)
PWM.add_channel_pulse(0, 17, 2000, 500)

import time
time.sleep(50) # delays for 5 seconds

# Stop PWM for specific GPIO on channel 0
PWM.clear_channel_gpio(0, 17)

# Shutdown all PWM and DMA activity
PWM.cleanup()
