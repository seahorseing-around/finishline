import RPi.GPIO as GPIO
import time

BEAM_PIN = 4
BUTTON_PIN = 17
RACE_ACTIVE = False
LED_PIN = 27

def break_beam_callback(channel):
    if GPIO.input(BEAM_PIN):
        print("beam unbroken")
    else:
        print("beam broken")
	RACE_ACTIVE = False

def button_callback(channel):
    print("Button was pushed!")
    RACE_ACTIVE = True
    i = 0
    GPIO.output(LED_PIN, GPIO.HIGH)
    while (RACE_ACTIVE):
        i += 1
        if not GPIO.input(BEAM_PIN):
            print("beam broken")
	    RACE_ACTIVE = False
            print(i)
            GPIO.output(LED_PIN, GPIO.LOW)
	time.sleep(0.001)
        pass
         

GPIO.setmode(GPIO.BCM)
GPIO.setup(BEAM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(BEAM_PIN, GPIO.BOTH, callback=break_beam_callback, bouncetime=200)

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.add_event_detect(BUTTON_PIN,GPIO.FALLING,callback=button_callback, bouncetime=200) # Setup event on pin 10 rising edge

GPIO.setup(LED_PIN, GPIO.OUT)

message = input("Press enter to quit\n\n")
GPIO.cleanup()