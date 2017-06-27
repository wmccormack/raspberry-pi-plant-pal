# Script to return sensor values for moisture, light, temperature and humidity.
# The script shall read the ADS1x15 analogue to digital converter (inputs are moisture
# prong and LDR) and Adafruit_DHT AM2302 sensor (temp and humidity)
import sys, time

# Import the ADS1x15 and Adafruit_DHT libraries for accessing the converter and AM sensor.
import Adafruit_ADS1x15, Adafruit_DHT

# Create an ADS1015 ADC (12-bit) instance.
adc = Adafruit_ADS1x15.ADS1015()

# Parse command line parameters for the AM2302 sensor.
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


# Choose a gain of 1 for reading voltages from 0 to 4.09V for the water moisture sensor.
# Or pick a different gain to change the range of voltages that are read:
#  - 2/3 = +/-6.144V
#  -   1 = +/-4.096V
#  -   2 = +/-2.048V
#  -   4 = +/-1.024V
#  -   8 = +/-0.512V
#  -  16 = +/-0.256V
# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
GAIN = 1

print('Reading moisture, light, temperature and humidity values, press Ctrl-C to quit...')
# Print nice channel column headers for each value
print('| Moisture | Light | Temp | Humidity |')
print('-' * 35)
# Main loop.
while True:
    # Call the read_retry method from the Adafruit_DHT module.
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    # Call the read_adc method from the Adafruit_ADS1x15 module for obtaining the moisture and light values.    
    moisture = adc.read_adc(0, gain=GAIN)
    light = adc.read_adc(1, gain=GAIN)
       
    # Print the sensor values.
    print('| {0:>6} | {1:>6} | {2:0.1f}* | {3:0.1f}% |'.format(moisture, light, temperature, humidity))
    # Pause for 5 seconds.
    time.sleep(5)
