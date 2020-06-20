from gpiozero import OutputDevice, Button
import time
from signal import pause

solenoid = OutputDevice(18)
button = Button(17)

def moo():
    print("on")
    solenoid.on

def baa():
    print("off")
    solenoid.off


button.when_pressed = solenoid.on
button.when_released = solenoid.off

pause()
