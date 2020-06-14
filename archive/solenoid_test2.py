import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

BUTTON_PIN=17
SOLENOID_PIN=18


def button_callback(channel):
    print("Button iwas pushed!")
    GPIO(SOLENOID_PIN,TRUE)
    sleep(20)
    GPIO(SOLENOID_PIN,False)

#General setup
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BCM)

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SOLENOID_PIN, GPIO.OUT)

GPIO.add_event_detect(BUTTON_PIN,GPIO.RISING,callback=button_callback) # Setup event on pin 10 rising edge

message = input("Press enter to quit\n\n") # Run until someone presses enter
GPIO.cleanup() # Clean up
