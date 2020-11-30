import threading
from gpiozero import SmoothedInputDevice
import logging
import time
import configparser

config_loc='/home/pi/finishline/config.properties'
config = configparser.RawConfigParser()
config.read(config_loc)
log_file = config.get('SystemConfig', 'log_file')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename=log_file)

RACE_TIMEOUT = config.getint('RaceConfig','race_timeout')

class Lane:
    def __init__(self, pin, colour, lane, error_led, race_finish_led, threshold, queue):
        self.pin = pin
        self.lane_sensor =  SmoothedInputDevice(pin, threshold=threshold, queue_len=queue)
        self.colour = colour
        self.lane_sensor._queue.start()
        self.lane = lane
        self.error_led = error_led
        self.race_finish_led = race_finish_led

    def is_active(self):
        active = self.lane_sensor.is_active
        return active
    
    def start_race(self, start_time):
        self.racing = True
        self.start_time = start_time
        x = threading.Thread(target = self.end_race)
        x.start()

    def end_race(self):
        logging.debug("{} started the race".format(self.colour))
        while self.is_active():
            pass 
        self.racing = False
        self.seconds = time.time() - self.start_time
        self.time = round(self.seconds,3)
        logging.info('Lane {}, {}, finished the race in {} seconds'.format(self.lane, self.colour, self.time))
        self.race_finish_led.blink(on_time=0.1, off_time=1, n=1)

    def timeout(self):
        logging.info("{} took too long, reached max timeout".format(self.colour))
        self.racing = False
        self.time = RACE_TIMEOUT
        logging.info('Lane {}, {}, did not finish (DNF)'.format(self.lane, self.colour))
        self.race_finish_led.blink(on_time=0.1, off_time=1, n=1)

    def is_racing(self):
        return self.racing

    def set_position(self,position):
        self.position = position
    
    def error_blink(self):
        self.error_led.blink(on_time=0.5, off_time=0.5, n=50)