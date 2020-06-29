from gpiozero import Button
import os
from signal import pause
import time
import logging
from subprocess import check_call

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='/var/log/derby_race.log')


def restart_race():
    logging.info("MANUAL RESTART")
    logging.info("Ending derby_race Service")
    os.system('sudo service derby_race stop')
    logging.info("Starting derby_race Service")
    os.system('sudo service derby_race start')

def shutdown():
    check_call(['sudo', 'poweroff'])


restart_btn = Button(26, hold_time=3)
restart_btn.when_pressed = restart_race
restart_btn.when_held = shutdown
pause()