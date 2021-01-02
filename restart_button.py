from gpiozero import Button
import os
from signal import pause
import time
import logging
from subprocess import check_call
import configparser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='/var/log/derby_race.log')

config_loc='/home/pi/finishline/config.properties'
config = configparser.RawConfigParser()
config.read(config_loc)

def restart_derby_race():
    logging.info("MANUAL RESTART")
    logging.info("Ending derby_race Service")
    os.system('sudo service derby_race stop')
    logging.info("Starting derby_race Service")
    os.system('sudo service derby_race start')

def shutdown():
    check_call(['sudo', 'poweroff'])

def toggle_derbynet():
    # UNTESTED
    # couldn't reliably trigger "when_held" - "when_pressed" took over
    logging.info("Toggling derbynet mode on/off")
    current_mode = config.getboolean('DerbyNetConfig','use_derbynet')
    logging.info("Current: USE_DERBYNET = {}".format(current_mode)) 
    config.set('DerbyNetConfig','use_derbynet', 'False' if current_mode else 'True')
    logging.info("New value USE_DERBYNET set")
    
    with open(config_loc, 'w') as configfile:
        config.write(configfile)
    
    logging.info("Config file written")
    
restart_btn = Button(26, hold_time=3)
restart_btn.when_held = toggle_derbynet
# restart_btn.when_pressed = restart_derby_race
pause()