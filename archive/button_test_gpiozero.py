from gpiozero import Button
from gpiozero import LED
from gpiozero import OutputDevice
from time import sleep


from signal import pause
button = Button(17)
led = LED(4)
trs = OutputDevice(18)
trs2 = OutputDevice(22,active_high=False)


def say_hello():
    print("Hello!")
    led.on()
    trs.on()
    trs2.on()
    sleep(2)
    led.off()
    trs.off()
    trs2.off()
    sleep(1)

button.when_pressed = say_hello

pause()