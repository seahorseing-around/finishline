from gpiozero import Button, LED, SmoothedInputDevice, OutputDevice
import statistics
from time import sleep
import threading
from signal import pause
import time
import logging
import requests
import xml.etree.ElementTree as ET
import operator
from signal import signal, SIGTERM, SIGINT
from sys import exit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='/var/log/derby_race.log')

THRESHOLD = 0.15
QUEUE = 5

PRIMER_BUTTON = Button(6)
START_BUTTON = Button(13)

SOLENOID = OutputDevice(16)
WHITE_LED = LED(18)
RED_LED = LED(25)
YELLOW_LED = LED(23)
GREEN_LED = LED(24)

ACTIVE_LED = LED(4)


URL = "https://ascoutin.london/derbynet"
USERNAME = "Timer"
PASSWORD = "doyourbest"

class Lane:
    def __init__(self, pin, colour, lane):
        self.pin = pin
        self.lane_sensor =  SmoothedInputDevice(pin, threshold=THRESHOLD, queue_len=QUEUE)
        self.colour = colour
        self.lane_sensor._queue.start()
        self.lane = lane

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
        YELLOW_LED.blink(on_time=0.1, off_time=1, n=1)

    def is_racing(self):
        return self.racing

    def set_position(self,position):
        self.position = position

def open_solenoid():
    logging.info("Opening Solenoid")
    SOLENOID.on()
    time.sleep(2)
    SOLENOID.off()


lanes = [
    Lane(17, "Yellow",2),
    Lane(5, "Blue",1),
    Lane(22, "Green",3),
    Lane(27, "White",4)
]

def derby_post(cookie_jar="",action = "timer-message",data={},message=""):
    logging.debug("Sending {} Request: {}".format(action,message))
    headers = {"Content-Type":"application/x-www-form-urlencoded"}
    data["action"] = action
    data["remote-start"] = "yes"
    if(len(message)>0):
        data["message"] = message
    if(len(cookie_jar)>0):
        x = requests.post("{}{}".format(URL,"/action.php"), headers = headers, data = data,cookies = cookie_jar)
    else:
        x = requests.post("{}{}".format(URL,"/action.php"), headers = headers, data = data)
    logging.debug(x.status_code)
    logging.debug(x.text)
    x.close()

    return x

def check_success(message,x):
    if ("<success/>" in x.text):
        logging.debug("{} Successful".format(message))
        return True
    elif ("</failure>" in x.text) :
        root = ET.fromstring(x.text)
        logging.error("{} Failed. Message = {}, code = {}".format(message,root.find("failure").text,root.find("failure").get("code")))
        return False

def check_abort(x):
    if("<abort/>" in x.text):
        logging.error("Heat aborted")
        return True
    else:
        return False

def login():
    data = {"name":USERNAME,"password":PASSWORD}
    x = derby_post(action = "login", data = data)
    logging.debug("Cookies received: {}".format(x.cookies))
    return x.cookies

def hello(cookie_jar):
    x = derby_post(cookie_jar = cookie_jar, message = "HELLO")
    if not check_success("HELLO",x):
        return


def heartbeat(cookie_jar):
    x = derby_post(cookie_jar = cookie_jar, message = "HEARTBEAT")
    
    if not check_success("HEARTBEAT",x):
        return

    if check_abort(x):
        return

    # get heat info
    root = ET.fromstring(x.text)

    if len(root.findall("heat-ready")) > 0 :
        logging.debug("Setting heat info")
        active_heat = {}
        active_heat["lane-mask"] = root.find("heat-ready").get("lane-mask")
        active_heat["class"] = root.find("heat-ready").get("class")
        active_heat["round"] = root.find("heat-ready").get("round")
        active_heat["roundid"] = root.find("heat-ready").get("roundid")
        active_heat["heat"] = root.find("heat-ready").get("heat")
        logging.info("This Heat: Class = {}, Round = {}, Heat = {}".format(active_heat["class"],active_heat["round"],active_heat["heat"]))
        return active_heat
    else:
        logging.info("No active heat")
        return False


def identified(cookie_jar, lane_count):
    x = derby_post(cookie_jar = cookie_jar, message = "IDENTIFIED",data = {"land_count":lane_count})
    
    if not check_success("IDENTIFIED",x):
        return

def started(cookie_jar):
    x = derby_post(cookie_jar = cookie_jar, message = "STARTED")
    
    if (not check_success("STARTED",x)) or check_abort(x):
        return False
    else:
        return True

def finished(cookie_jar,results,active_heat):
    results["roundid"] = active_heat["roundid"]
    results["heat"] = active_heat["heat"]
    x = derby_post(cookie_jar = cookie_jar, message = "FINISHED",data = results)
    logging.debug(x.text)
    if not check_success("FINISHED",x):
        return

    if check_abort(x):
        return
    

def malfunction(cookie_jar,detectable, error_message):
    malfunction_data = {"detectable":detectable,"error":error_message}
    x = derby_post(cookie_jar = cookie_jar, message = "MALFUNCTION",data = malfunction_data)
    
    if not check_success("MALFUNCTION",x):
        return

def race():
    separator()
    logging.info("Preparing for Race")
    WHITE_LED.on()
    separator()
    # Check lanes are all operational
    logging.info("Checking Track")
    for lane in lanes:
        if lane.is_active():
            logging.debug("{} is active".format(lane.colour))
        else:
            logging.error ("{} NOT active".format(lane.colour))

    # Report if a lane is broken
    for lane in lanes:
        if not lane.is_active():
            logging.error("{} lane broken, aborting race".format(lane.colour))
            abort_race("lane_broken")
            return
    logging.info("Track ready to race")

    #Setup Derbynet
    logging.info("Initiating DerbyNet")
    #login
    cookie_jar = login()
    if len(cookie_jar) < 1:
        logging.error("DerbyNet login failed")
        abort_race()
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
            abort_race()
            return
    else:
        logging.error("Race failed: No active heat")
        abort_race("no_active_heat")
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

def separator():
    logging.info("--------------------------------------")

def abort_race(reason):
    RED_LED.off()
    YELLOW_LED.off()
    GREEN_LED.off()
    WHITE_LED.off()
    if reason == "no_active_heat":
        RED_LED.blink(on_time=0.5, off_time=0.5, n=3)
    elif reason == "lane_broken":
        RED_LED.blink(on_time=0.025, off_time=0.025, n=20)
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