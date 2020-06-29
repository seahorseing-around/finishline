from gpiozero import Button
import os
from signal import pause
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='/var/log/derby_race.log')


def restart_race():
    logging.info("MANUAL RESTART")
    os.system('sudo service derby_race stop')
    time.sleep(1)
    os.system('sudo service derby_race start')

restart_btn = Button(26, hold_time=2)
restart_btn.when_held = restart_race
pause()