from gpiozero import Button, LED, OutputDevice
import statistics
from time import *
import time
from signal import pause
import threading
import logging
import operator
from signal import signal, SIGTERM, SIGINT
from sys import exit
from requests import ConnectTimeout, ConnectionError
import configparser
from Lanes import Lane
from derby_net_integration import *

config_loc='/home/pi/finishline/config.properties'
config = configparser.RawConfigParser()
config.read(config_loc)
log_file = config.get('SystemConfig', 'log_file')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename=log_file)

# Race Tuning
THRESHOLD = config.getfloat('RaceConfig','threshold')
QUEUE = config.getint('RaceConfig','queue')

# LED's 
WHITE_LED = LED(config.getint('RaceConfig','white_led'))
RED_LED = LED(config.getint('RaceConfig','red_led'))
YELLOW_LED = LED(config.getint('RaceConfig','yellow_led'))
GREEN_LED = LED(config.getint('RaceConfig','green_led'))
ACTIVE_LED = LED(config.getint('RaceConfig','active_led'))

# Lanes
YELLOW_LANE = config.getint('RaceConfig','yellow_lane')
BLUE_LANE = config.getint('RaceConfig','blue_lane')
GREEN_LANE = config.getint('RaceConfig','green_lane')
WHITE_LANE = config.getint('RaceConfig','white_lane')

SEP = "---------------"

# # # # # # # # # # # # # #
# Initiate Lanes
# # # # # # # # # # # # # #

lanes = [
    Lane(WHITE_LANE, "White",4, WHITE_LED, YELLOW_LED, THRESHOLD, QUEUE),
    Lane(GREEN_LANE, "Green",3, GREEN_LED, YELLOW_LED, THRESHOLD, QUEUE),
    Lane(YELLOW_LANE, "Yellow",2, YELLOW_LED, YELLOW_LED, THRESHOLD, QUEUE),
    Lane(BLUE_LANE, "Blue",1, RED_LED, YELLOW_LED, THRESHOLD, QUEUE)
]

# # # # # # # # # # # # # #
# Race Functions
# # # # # # # # # # # # # #

def test():
    while True:
        logging.info("{} = {}, {} = {}, {} = {}, {} = {}".format(
            lanes[0].colour, "1" if lanes[0].is_active() else "0",
            lanes[1].colour, "1" if lanes[1].is_active() else "0",
            lanes[2].colour, "1" if lanes[2].is_active() else "0",
            lanes[3].colour, "1" if lanes[3].is_active() else "0"
        ) )
        sleep(0.5)


if __name__ == '__main__':
    logging.info("{} Derby Pi Running Test! {}".format(SEP,SEP))
    test()