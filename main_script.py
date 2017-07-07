import sys, time
import Adafruit_ADS1x15, Adafruit_DHT
import requests



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

print('Reading moisture, light, temperature and humidity values, press Ctrl-C to quit...')
# Print nice channel column headers for each value
print('| Moisture | Light | Temp | Humidity |')
print('-' * 35)

    # Main loop.
while True:
            # Call the read_retry method from the Adafruit_DHT module.
            humidity_reading, temperature_reading = Adafruit_DHT.read_retry(sensor, pin)

            # Call the read_adc method from the Adafruit_ADS1x15 module for obtaining the moisture and light values.    
            moisture_reading = adc.read_adc(0, gain=GAIN)
            light_reading = adc.read_adc(1, gain=GAIN)

            # Prepare the readings for HTTP Post Request. Post cannot take a float therefore to maintain accurate values
            # we multiply up by 10 and divide by 10.0 at the server side. 
            moisture = int(moisture_reading)
            light = int(light_reading)
            temperature = int(temperature_reading*10)
            humidity = int(humidity_reading*10)
            
       
            # Print the sensor values.
            print('| {0:>6} | {1:>6} | {2:0.1f}* | {3:0.1f}% |'.format(moisture, light, temperature, humidity))

            payload ={'Moisture':moisture,'Light':light,'Temp':temperature,'Humid':humidity}

            r = requests.post("http://wmccormack.pythonanywhere.com/readings/pidata/", data=payload) 
            # Pause for 5 seconds.
            time.sleep(5)
