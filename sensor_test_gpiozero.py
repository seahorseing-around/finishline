from gpiozero import Button
from gpiozero import LED
from gpiozero import SmoothedInputDevice
import statistics
from time import sleep
import threading
from signal import pause
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

THRESHOLD = 0.15
QUEUE = 5

BUTTON = Button(17)
LED = LED(4)

class Lane:
    def __init__(self, pin, colour):
        self.pin = pin
        self.lane_sensor =  SmoothedInputDevice(pin, threshold=THRESHOLD, queue_len=QUEUE)
        self.colour = colour
        self.lane_sensor._queue.start()

    def is_active(self):
        active = self.lane_sensor.is_active
        return active
    
    def start_race(self, start_time):
        self.racing = True
        self.start_time = start_time
        x = threading.Thread(target = self.end_race)
        x.start()

    def end_race(self):
        logging.info("{} started the race".format(self.colour))
        while self.is_active():
            pass 
        self.racing = False
        self.seconds = time.time() - self.start_time
        self.time = round(self.seconds,2)
        logging.info('{} finished the race'.format(self.colour, self.time))

    def is_racing(self):
        return self.racing

lanes = [
    Lane(24, "Yellow"),
    Lane(27, "Blue"),
    Lane(23, "Green"),
    Lane(22, "White")
]

def race():
    separator()
    logging.info("Preparing for Race")
    separator()
    # Check lanes are all operational
    for lane in lanes:
        if lane.is_active():
            logging.info("{} is active".format(lane.colour))
        else:
            logging.error ("{} NOT active".format(lane.colour))
    separator()

    # Report if a lane is broken
    for lane in lanes:
        if not lane.is_active():
            logging.error("{} lane broken, aborting race".format(lane.colour))
            LED.off()
            LED.blink(on_time=0.1, off_time=0.1, n=5)
            separator()
            return

    # Start Race
    logging.info("Race Started!")
    separator()
    LED.on()
    start_time = time.time()
    for lane in lanes:
        lane.start_race(start_time)

    # Open Solenoid
    # TODO

    # Poll for the end of the race
    RACE_ACTIVE = True
    while RACE_ACTIVE:
        RACE_ACTIVE = False
        for lane in lanes:
            if lane.is_racing():
                RACE_ACTIVE = True
    end_race(lanes)
    logging.info("Race Complete!")    
    separator()

def end_race(lanes):
    winner = lanes[0]
    for lane in lanes:
        logging.info ("{} took {}".format(lane.colour, lane.time))
        if lane.seconds < winner.seconds:
            winner = lane
    separator()
    logging.info("*** {} Won! ***".format(lane.colour))
    separator()
    LED.off()
    return False

def separator():
    logging.info("--------------------------------------")

BUTTON.when_pressed = race

race()
pause()