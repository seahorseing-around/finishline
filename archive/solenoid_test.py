import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library



def button_callback(channel):
    print("Button was pushed!")
    GPIO(18, True)
    sleep(2)
    GPIO(18,False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
message = input("Press enter to quit\n\n") # Run until someone presses enter
GPIO.cleanup() # Clean up
