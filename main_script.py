import sys, time
import Adafruit_ADS1x15, Adafruit_DHT
import requests
import RPi.GPIO as GPIO



adc = Adafruit_ADS1x15.ADS1015()

sensor_args = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }
if len(sys.argv) == 3 and sys.argv[1] in sensor_args:
    sensor = sensor_args[sys.argv[1]]
    pin = sys.argv[2]
else:
    print('usage: sudo ./Adafruit_DHT.py [11|22|2302] GPIOpin#')
    print('example: sudo ./Adafruit_DHT.py 2302 4 - Read from an AM2302 connected to GPIO #4')
    sys.exit(1)

GAIN = 1

pi_id = 1

# Function to read and upload sensor data to the web application.
def data_function():
        
    # Call the read_retry method from the Adafruit_DHT module.
    try:
        humidity_reading, temperature_reading = Adafruit_DHT.read_retry(sensor, pin)
    except:
        error_log = {'Error':'There was an error at the pi end with reading temp and humidity values'}
        r = requests.post("http://wmccormack.pythonanywhere.com/errors/", data=error_log)

    # Call the read_adc method from the Adafruit_ADS1x15 module for obtaining the moisture and light values.
    try:
        moisture_reading = adc.read_adc(0, gain=GAIN)
    except:
        error_log = {'Error':'There was an error at the pi end with reading moisture values'}
        r = requests.post("http://wmccormack.pythonanywhere.com/errors/", data=error_log)
    try:
        light_reading = adc.read_adc(1, gain=GAIN)
    except:
        error_log = {'Error':'There was an error at the pi end with reading light values'}
        r = requests.post("http://wmccormack.pythonanywhere.com/errors/", data=error_log)

    # Prepare the readings for HTTP Post Request. To maintain data integrity
    # we multiply up by 10 and divide by 10.0 at the server side (if needed)
    # in the case of temperature and humidity. Therefore no rounding issues.
    moisture = int(moisture_reading)
    light = int(light_reading)
    temperature = int(temperature_reading*10)
    humidity = int(humidity_reading*10)

    
    # Print the sensor values to screen (if a screen is attached to the plant monitoring station).
    print('| {0:>6} | {1:>6} | {2:0.1f}* | {3:0.1f}% |'.format(moisture, light, temperature, humidity))
    # Prepare the data payload.
    payload ={'Identification':pi_id,'Moisture':moisture,'Light':light,'Temp':temperature,'Humid':humidity}

    try:
        r = requests.post("http://wmccormack.pythonanywhere.com/readings/", data=payload)
        # Pause for 2 seconds.
        time.sleep(2)
    except:
        error_log = {'Error':'There was an error at the pi end with uploading data to the application'}
        r = requests.post("http://wmccormack.pythonanywhere.com/errors/", data=error_log)

# Function to check if the plant requires water and if so, activate the waterer. Lastly, the function sends
# notification to the web application that the plant was watered. 
def watering_function():            
    watering_payload = {'Identification': pi_id}

    try:
        w = requests.post("http://wmccormack.pythonanywhere.com/watering/plant_communication/", data=watering_payload)
    except:
        error_log = {'Error':'There was an error at the pi end with checking for watering notification'}
        r = requests.post("http://wmccormack.pythonanywhere.com/errors/", data=error_log)

    try:
        if w.content=="Water!":
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            GPIO.setup(11, GPIO.OUT)
            GPIO.output(11, GPIO.HIGH)
            time.sleep(1)
            GPIO.cleanup()
            n = requests.post("http://wmccormack.pythonanywhere.com/notifications/", data=watering_payload) 
        else:
            print "Nope"
    except:
        error_log = {'Error':'There was an error at the pi end with activating the water mechanism'}
        r = requests.post("http://wmccormack.pythonanywhere.com/errors/", data=error_log)
        
loop=0
while True:
    # Set a loop so that watering check is carried out every 2 hours whilst readings
    # are taken hourly.
    data_function()
    if loop%2 != 0:
        watering_function()
    else:
        pass
    loop+=1
    time.sleep(3600)

            
