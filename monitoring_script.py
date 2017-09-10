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

pi_id = 2

# Polling interval is set to 3600 seconds (1 hour in normal circumstances). For the demo the default is 10 seconds.
interval = 10

# Function to read and upload sensor data to the web application.
def data_function():
        
    # Call the read_retry method from the Adafruit_DHT module.
    try:
        humidity_reading, temperature_reading = Adafruit_DHT.read_retry(sensor, pin)
    except Exception as e:
        error_log = {'Error':"There was an error at Monitoring Station {}. Specifically {}".format(pi_id, e)}
        error_request = requests.post("http://wmccormack.pythonanywhere.com/errors/errors/", data=error_log)

    # Call the read_adc method from the Adafruit_ADS1x15 module for obtaining the moisture and light values.
    try:
        moisture_reading = adc.read_adc(0, gain=GAIN)
    except Exception as e:
        error_log = {'Error':"There was an error at Monitoring Station {}. Specifically {}".format(pi_id, e)}
        error_request = requests.post("http://wmccormack.pythonanywhere.com/errors/errors/", data=error_log)
    try:
        light_reading = adc.read_adc(1, gain=GAIN)
    except Exception as e:
        error_log = {'Error':"There was an error at Monitoring Station {}. Specifically {}".format(pi_id, e)}
        error_request = requests.post("http://wmccormack.pythonanywhere.com/errors/errors/", data=error_log)

    # Prepare the readings for HTTP Post Request. To maintain data integrity
    # we multiply up by 10 and divide by 10.0 at the server side (if needed)
    # in the case of temperature and humidity. Therefore no rounding issues.
    try:
        moisture = int(moisture_reading)
        light = int(light_reading)
        temperature = int(temperature_reading*10)
        humidity = int(humidity_reading*10)
    except (TypeError, Exception) as e:
        error_log = {'Error':"There was an error at Monitoring Station {}. Specifically {}. Values have been defaulted on this occasion but check the station for loose cables.".format(pi_id, e)}
        error_request = requests.post("http://wmccormack.pythonanywhere.com/errors/errors/", data=error_log)
        moisture = 1100
        light = 900
        temperature = 230
        humidity = 600

    
    # Print the sensor values to screen (if a screen is attached to the plant monitoring station).
    print('| {0:>6} | {1:>6} | {2:0.1f}* | {3:0.1f}% |'.format(moisture, light, temperature, humidity))
    # Prepare the data payload.
    payload ={'Identification':pi_id,'Moisture':moisture,'Light':light,'Temp':temperature,'Humid':humidity}

    try:
        data_request = requests.post("http://wmccormack.pythonanywhere.com/readings/", data=payload)

        # data_request returns the polling interval from the application. Update the global interval here.
        global interval
        interval = int(data_request.content)
        
        # Pause for 2 seconds.
        time.sleep(2)
    except Exception as e:
        error_log = {'Error':"There was an error at Monitoring Station {}. Specifically {}".format(pi_id, e)}
        error_request = requests.post("http://wmccormack.pythonanywhere.com/errors/errors/", data=error_log)

# Function to check if the plant requires water and if so, activate the waterer. Lastly, the function sends
# notification to the web application that the plant was watered. 
def watering_function():            
    watering_payload = {'Identification': pi_id}

    try:
        water_request = requests.post("http://wmccormack.pythonanywhere.com/watering/plant_communication/", data=watering_payload)
    except Exception as e:
        error_log = {'Error':"There was an error at Monitoring Station {}. Specifically {}".format(pi_id, e)}
        error_request = requests.post("http://wmccormack.pythonanywhere.com/errors/errors/", data=error_log)

    try:
        if water_request.content=="Water!":
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            GPIO.setup(11, GPIO.OUT)
            GPIO.output(11, GPIO.HIGH)
            time.sleep(1)
            GPIO.cleanup()
            notify_request = requests.post("http://wmccormack.pythonanywhere.com/notifications/", data=watering_payload) 
        else:
            print "No watering."
    except Exception as e:
        error_log = {'Error':"There was an error at Monitoring Station {}. Specifically {}".format(pi_id, e)}
        error_request = requests.post("http://wmccormack.pythonanywhere.com/errors/errors/", data=error_log)
        
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
    # Interval will either be the default or a modified value from the application.
    time.sleep(interval)

            
