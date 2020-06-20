import requests
import logging
import xml.etree.ElementTree as ET
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

URL = "https://ascoutin.london/derbynet"
USERNAME = "Timer"
PASSWORD = "doyourbest"
COOKIE_JAR = ""

def derby_post(action = "timer-message",data={},message=""):
    logging.info("Sending {} Request: {}".format(action,message))
    headers = {"Content-Type":"application/x-www-form-urlencoded"}
    data["action"] = action
    data["remote-start"] = "yes"
    if(len(message)>0):
        data["message"] = message
    if(len(COOKIE_JAR)>0):
        x = requests.post("{}{}".format(URL,"/action.php"), headers = headers, data = data,cookies = COOKIE_JAR)
    else:
        x = requests.post("{}{}".format(URL,"/action.php"), headers = headers, data = data)
    logging.debug(x.status_code)
    logging.debug(x.text)
    x.close()

    return x

def check_success(message,x):
    if ("<success/>" in x.text):
        logging.info("{} Successful".format(message))
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
    logging.info("Cookies received: {}".format(x.cookies))
    return x.cookies

def hello():
    x = derby_post(message = "HELLO")
    if not check_success("HELLO",x):
        return


def heartbeat():
    x = derby_post(message = "HEARTBEAT")
    
    if not check_success("HEARTBEAT",x):
        return

    if check_abort(x):
        return

    # get heat info
    root = ET.fromstring(x.text)

    if len(root.findall("heat-ready")) > 0 :
        logging.info("Setting heat info")
        ACTIVE_HEAT = {}
        ACTIVE_HEAT["lane-mask"] = root.find("heat-ready").get("lane-mask")
        ACTIVE_HEAT["class"] = root.find("heat-ready").get("class")
        ACTIVE_HEAT["round"] = root.find("heat-ready").get("round")
        ACTIVE_HEAT["roundid"] = root.find("heat-ready").get("roundid")
        ACTIVE_HEAT["heat"] = root.find("heat-ready").get("heat")
        logging.info("This Heat: Class = {}, Round = {}, Heat = {}".format(ACTIVE_HEAT["class"],ACTIVE_HEAT["round"],ACTIVE_HEAT["heat"]))
        return ACTIVE_HEAT
    else:
        logging.info("No active heat")
        return False


def identified(lane_count):
    x = derby_post(message = "IDENTIFIED",data = {"land_count":lane_count})
    
    if not check_success("IDENTIFIED",x):
        return

def started():
    x = derby_post(message = "STARTED")
    
    if (not check_success("STARTED",x)) or check_abort(x):
        return False
    else:
        return True

def finished(results):
    results["roundid"] = ACTIVE_HEAT["roundid"]
    results["heat"] = ACTIVE_HEAT["heat"]
    x = derby_post(message = "FINISHED",data = results)
    
    if not check_success("FINISHED",x):
        return

    if check_abort(x):
        return
    

def malfunction(detectable, error_message):
    malfunction_data = {"detectable":detectable,"error":error_message}
    x = derby_post(message = "MALFUNCTION",data = malfunction_data)
    
    if not check_success("MALFUNCTION",x):
        return

def race(ACTIVE_HEAT):
    logging.info("Stating Race!")
    if ACTIVE_HEAT:
        if started():
            results = {
                "lane1":"1.11",
                "place1":"1",
                "lane2":"2.22",
                "place2":"2",
                "lane3":"3.33",
                "place3":"3",
                "lane4":"4.44",
                "place4":"4"
            }
            finished(results)
        else:
            logging.error("Race Failed")
    else:
        logging.error("Race failed: No active heat")

COOKIE_JAR = login()

hello()
ACTIVE_HEAT = heartbeat()
identified(4)
race(ACTIVE_HEAT)
#malfunction(0,"generic error")
