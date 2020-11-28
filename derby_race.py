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
log_file = config.get('RaceConfig', 'log_file')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename=log_file)

# Race Tuning
THRESHOLD = 0.15
QUEUE = int(config.get('RaceConfig','queue'))

# Buttons & Solenoid Config
PRIMER_BUTTON = Button(int(config.get('RaceConfig','primer_button')))
START_BUTTON = Button(int(config.get('RaceConfig','start_button')))
SOLENOID = OutputDevice(int(config.get('RaceConfig','solenoid')))

# LED's 
WHITE_LED = LED(int(config.get('RaceConfig','white_led')))
RED_LED = LED(int(config.get('RaceConfig','red_led')))
YELLOW_LED = LED(int(config.get('RaceConfig','yellow_led')))
GREEN_LED = LED(int(config.get('RaceConfig','green_led')))
ACTIVE_LED = LED(int(config.get('RaceConfig','active_led')))

# Lanes
YELLOW_LANE = int(config.get('RaceConfig','yellow_lane'))
BLUE_LANE = int(config.get('RaceConfig','blue_lane'))
GREEN_LANE = int(config.get('RaceConfig','green_lane'))
WHITE_LANE = int(config.get('RaceConfig','white_lane'))

# DerbyNet Config
USE_DERBYNET = bool(config.get('DerbyNetConfig','use_derbynet'))

# Timings
SOLENOID_OPEN_TIME = int(config.get('RaceConfig','solenoid_open'))

def open_solenoid():
    logging.info("Opening Solenoid")
    SOLENOID.on()
    time.sleep(SOLENOID_OPEN_TIME)
    SOLENOID.off()

# # # # # # # # # # # # # #
# Initiate Lanes
# # # # # # # # # # # # # #

lanes = [
    Lane(YELLOW_LANE, "Yellow",2, YELLOW_LED, YELLOW_LED, THRESHOLD, QUEUE),
    Lane(BLUE_LANE, "Blue",1, RED_LED, YELLOW_LED, THRESHOLD, QUEUE),
    #Lane(GREEN_LANE, "Green",3, GREEN_LED, YELLOW_LED, THRESHOLD, QUEUE),
    Lane(YELLOW_LANE, "White",4, WHITE_LED, YELLOW_LED, THRESHOLD, QUEUE)
]

# # # # # # # # # # # # # #
# Initiate Lanes
# # # # # # # # # # # # # #

def race():
    separator()
    logging.info("Preparing for Race")
    separator()
    # Check lanes are all operational
    logging.info("Checking Track")
    for lane in lanes:
        if lane.is_active():
            logging.debug("{} is active".format(lane.colour))
        else:
            logging.error ("{} NOT active".format(lane.colour))
            lane.error_blink()

    # Report if a lane is broken
    for lane in lanes:
        if not lane.is_active():
            logging.error("{} lane broken, aborting race".format(lane.colour))
            abort_race("lane_broken")
            return
    logging.info("Track ready to race")

    #indicate prep has begun
    WHITE_LED.on()

    #Setup Derbynet
    logging.info("Initiating DerbyNet")
    
    try:
        if USE_DERBYNET:
            #login
            cookie_jar = login()
            if len(cookie_jar) < 1:
                logging.error("DerbyNet login failed")
                abort_race("DerbyNet login failed")
                return
            #tell derbynet how many lanes there are
            #identified(cookie_jar=cookie_jar, lane_count=len(lanes))
            
            #Preliminary call to initiate racing
            hello(cookie_jar)

            #get heat information
            active_heat = heartbeat(cookie_jar)

        # Start Race
        if active_heat:
            if started(cookie_jar):
                separator()
                logging.info("Ready to race!")
                separator()
                YELLOW_LED.on()
                # WAIT for start button press 
                # For some reason button.wait_for_press didn't work
                while (not START_BUTTON.is_pressed):
                    time.sleep(0.1)
                logging.info("Starting race")
                YELLOW_LED.off()
                WHITE_LED.off()
                GREEN_LED.on()

                start_time = time.time()
                for lane in lanes:
                    lane.start_race(start_time)
                # Open Solenoid
                x = threading.Thread(target = open_solenoid())
                x.start()
                # Poll for the end of the race
                RACE_ACTIVE = True
                while RACE_ACTIVE:
                    RACE_ACTIVE = False
                    for lane in lanes:
                        if lane.is_racing():
                            RACE_ACTIVE = True
                results = end_race(lanes)  
                if USE_DERBYNET:
                    finished(cookie_jar = cookie_jar,results=results, active_heat=active_heat)
    
                logging.info("Class {}, Round {}, Heat {}. Race Complete!".format(active_heat["class"],active_heat["round"],active_heat["heat"]))
                WHITE_LED.blink(on_time=0.25, off_time=1, n=3)
                time.sleep(0.25)
                RED_LED.blink(on_time=0.25, off_time=1, n=3)
                time.sleep(0.25)
                YELLOW_LED.blink(on_time=0.25, off_time=1, n=3)
                time.sleep(0.25)
                GREEN_LED.blink(on_time=0.25, off_time=1, n=3)  
                separator()

            else:
                logging.error("Race Failed, couldn't start race")
                abort_race("couldn't reach DerbyNET")
                return
        else:
            logging.error("Race failed: No active heat")
            abort_race("no_active_heat")
            return
    
    except ConnectTimeout as et:
        abort_race("Couldn't contact DerbyNet")
        return 
    except ConnectionError as e:
        abort_race("Couldn't contact DerbyNet")
        return

def end_race(lanes):
    #Work out order
    sort_lanes_by_time = sorted(lanes,key =operator.attrgetter("time"))
    results={}
    i=1
    for lane in sort_lanes_by_time:
        lane.set_position(i)
        i+=1
        results["lane{}".format(lane.lane)]=lane.time
        results["place{}".format(lane.lane)]=lane.position
    separator()
    logging.info("*** Lane {}, {}, Won! ***".format(sort_lanes_by_time[0].lane,sort_lanes_by_time[0].colour))
    separator()
    GREEN_LED.off()
    return results

def abort_race(reason):
    sleep(3)
    RED_LED.off()
    YELLOW_LED.off()
    GREEN_LED.off()
    WHITE_LED.off()
    if reason == "no_active_heat":
        RED_LED.blink(on_time=0.5, off_time=0.5, n=3)
    elif reason == "lane_broken":
        RED_LED.blink(on_time=0.025, off_time=0.025, n=4)
    else:
        RED_LED.blink(on_time=0.1, off_time=0.1, n=5)
    
    return

def handler(signal_received, frame):
    # Handle any cleanup here
    RED_LED.off()
    YELLOW_LED.off()
    GREEN_LED.off()
    WHITE_LED.off()
    ACTIVE_LED.off()

    logging.info('Terminataion signal recieved, ending Derby Race')
    exit(0)

def separator():
    logging.info("--------------------------------------")

if __name__ == '__main__':
    # Tell Python to run the handler() function when SIGTERM is recieved
    signal(SIGTERM, handler)
    signal(SIGINT, handler)

    separator()
    logging.info("Derby Pi Starting up!")
    separator()

    ACTIVE_LED.on()
    PRIMER_BUTTON.when_pressed = race
    START_BUTTON.when_pressed = open_solenoid
    pause()