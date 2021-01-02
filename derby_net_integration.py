import requests
import xml.etree.ElementTree as ET
import logging
import configparser

config_loc='/home/pi/finishline/config.properties'
config = configparser.RawConfigParser()
config.read(config_loc)
log_file = config.get('SystemConfig', 'log_file')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename=log_file)


URL = config.get('DerbyNetConfig','url')
USERNAME = config.get('DerbyNetConfig','username')
PASSWORD = config.get('DerbyNetConfig','password')

# # # # # # # # # # # # # #
# DerbyNet Integration
# # # # # # # # # # # # # #

def derby_post(cookie_jar="",action = "timer-message",data={},message=""):
    logging.debug("Sending {} Request: {}".format(action,message))
    headers = {"Content-Type":"application/x-www-form-urlencoded"}
    data["action"] = action
    data["remote-start"] = "yes"
    if(len(message)>0):
        data["message"] = message

    if(len(cookie_jar)>0):
        x = requests.post("{}{}".format(URL,"/action.php"), headers = headers, data = data,cookies = cookie_jar, timeout = 2, verify=False)
    else:
        x = requests.post("{}{}".format(URL,"/action.php"), headers = headers, data = data, timeout = 2,  verify=False)
    logging.debug(x.status_code)
    logging.debug(x.text)
    x.close()
    
    return x


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

# # # # # # # # # # # # # #
# Read DerbyNet Responses 
# # # # # # # # # # # # # #

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