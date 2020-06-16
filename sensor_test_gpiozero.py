from gpiozero import Button
from gpiozero import LED
from gpiozero import SmoothedInputDevice
from time import sleep
from signal import pause
import time

THRESHOLD = 0.25

BUTTON = Button(17)
LED = LED(4)

class Lane:
    def __init__(self, pin, colour):
        self.pin = pin
        self.lane_sensor =  SmoothedInputDevice(pin, threshold=THRESHOLD)
        self.colour = colour
        self.lane_sensor._queue.start()

    def is_active(self):
        active = self.lane_sensor.is_active
        return active
    
    def start_race(self):
        self.racing = True

    def end_race(self, start_time):
        self.racing = False
        self.end_time = time.time()
        self.seconds = self.end_time - start_time
        self.time = round(self.seconds,2)
        print('{} finished the race!'.format(self.colour, self.time))

    def is_racing(self):
        return self.racing

lanes = [
    Lane(23, "Yellow"),
    Lane(27, "Blue"),
    Lane(24, "Green"),
    Lane(22, "White")
]

def race():
    print("Checking lanes")
    # Check lanes are all operational
    for lane in lanes:
        print(lane.colour + " is active: " + str(lane.is_active()))
        if not lane.is_active():
            print(lane.colour + " lane broken, aborting race")
            LED.off()
            LED.blink(on_time=0.1, off_time=0.1, n=5)
            return       

    # Start Race
    print("Race Started!")
    RACE_ACTIVE = True
    LED.on()
    start_time = time.time()
    for lane in lanes:
        lane.start_race()

    # Open Solenoid
    # TODO

    # poll for times
    RACE_ACTIVE = True
    while RACE_ACTIVE:
        RACE_ACTIVE = False
        for lane in lanes:
            if lane.is_racing():
                if lane.is_active():
                    RACE_ACTIVE = True
                else:
                    lane.end_race(start_time)

    print("Race Complete!")

    for lane in lanes:
        print ("{} took {}".format(lane.colour, lane.time))

def end_race(lane,seconds):
    print(lane + " Won!")
    print(seconds/100.0)
    LED.off()
    return False

def check_active(lane):
    if lane.is_active:
        print(lane.colour + " is active")
    else:
        print (lane.colour + " NOT active")

BUTTON.when_pressed = race

race()
pause()

