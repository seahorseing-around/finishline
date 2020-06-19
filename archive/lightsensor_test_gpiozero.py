from gpiozero import Button
from gpiozero import LED
from gpiozero import LightSensor
from time import sleep
from signal import pause
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

BUTTON = Button(17)
LED = LED(4)

class Lane:
    def __init__(self, pin, colour):
        self.pin = pin
        self.lane_sensor =  LightSensor(pin, threshold=0.1, queue_len=100)
        self.colour = colour
        #self.lane_sensor._queue.start()

    def is_active(self):
        active = self.lane_sensor.is_active
        return active
    
    def start_race(self, start_time):
        self.start_time = start_time
        self.racing = True
        self.lane_sensor.when_dark = self.end_race

    def end_race(self):
        self.racing = False
        self.seconds = time.time() - self.start_time
        self.time = round(self.seconds,2)
        logging.info('{} finished the race!'.format(self.colour, self.time))

    def is_racing(self):
        return self.racing

lanes = [
    Lane(24, "Yellow"),
    Lane(27, "Blue"),
    Lane(23, "Green"),
    Lane(22, "White")
]

def race():
    logging.info("Checking lanes")
    # Check lanes are all operational
    for lane in lanes:
        if lane.is_active():
            logging.info(lane.colour + " is active")
        else:
            logging.error (lane.colour + " NOT active")

    for lane in lanes:
        if not lane.is_active():
            logging.error(lane.colour + " lane broken, aborting race")
            LED.off()
            LED.blink(on_time=0.1, off_time=0.1, n=5)
            return       

    # Start Race
    logging.info("Race Started!")
    RACE_ACTIVE = True
    LED.on()
    start_time = time.time()
    for lane in lanes:
        lane.start_race(start_time)

    # Open Solenoid
    # TODO

    # poll for times
    RACE_ACTIVE = True
    while RACE_ACTIVE:
        RACE_ACTIVE = False
        for lane in lanes:
            if lane.is_racing():
                if lane.lane_sensor.value < 0.1:
                    print(lane.colour + " " + str(lane.lane_sensor.value))
                RACE_ACTIVE = True

    logging.info("Race Complete!")

    for lane in lanes:
        logging.info ("{} took {}".format(lane.colour, lane.time))

def end_race(lane,seconds):
    logging.info(lane + " Won!")
    logging.info(seconds/100.0)
    LED.off()
    return False

BUTTON.when_pressed = race

race()
pause()