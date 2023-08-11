import Adafruit_DHT
import RPi.GPIO as GPIO
import gspread
import time
import math
from oauth2client.service_account import ServiceAccountCredentials

GPIO.setmode(GPIO.BCM)
DHT_SENSOR_PIN = 23
dht_sensor = Adafruit_DHT.DHT11
mq6_pin = 17     
buzzer_pin = 27  
MQ135_PIN = 22
fan = 9
pin_to_circuit = 10

AQI_BREAKPOINTS = [0, 12.0, 35.4, 55.4, 150.4, 250.4, 350.4, 500.4]
AQI_THRESHOLDS = [
    (0, 50),
    (51, 100),
    (101, 150),
    (151, 200),
    (201, 300),
    (301, 400),
    (401, 500)]
AQI_FORMULA_PARAMS = [
    (0, 50, 0, 12, "PM2.5"),
    (51, 100, 12.1, 35.4, "PM2.5"),
    (101, 150, 35.5, 55.4, "PM2.5"),
    (151, 200, 55.5, 150.4, "PM2.5"),
    (201, 300, 150.5, 250.4, "PM2.5"),
    (301, 400, 250.5, 350.4, "PM2.5"),
    (401, 500, 350.5, 500.4, "PM2.5")]

GPIO.setwarnings(False)
GPIO.setup(mq6_pin, GPIO.IN)
GPIO.setup(buzzer_pin, GPIO.OUT)
GPIO.setup(fan, GPIO.OUT)
temp_threshold = 25

SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = '/home/pi/Desktop/weather-monitoring-390112-506f6ae162a5.json'  
SPREADSHEET_ID = '18GPJ_rGcJjmUZcb8qEfUpGlUm1WWmHG2lLQH8SKCdJg' 
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.sheet1  

def read_gas_percentage():
    sensor_value = GPIO.input(mq6_pin)
    gas_percentage = ((sensor_value / 1023) * 100)
    return gas_percentage
  
def heat_sensor():
    GPIO.setup(MQ135_PIN, GPIO.OUT)
    GPIO.output(MQ135_PIN, GPIO.HIGH)
    time.sleep(30)

def read_sensor():
    GPIO.setup(MQ135_PIN, GPIO.IN)
    time.sleep(10)
    value = GPIO.input(MQ135_PIN)
    return value
    
def calculate_aqi(value):
    ppm = (value / 1024.0) * 10.0
    for i, (lb, ub) in enumerate(AQI_THRESHOLDS):
        if lb <= ppm <= ub:
            (iaqi_lb, iaqi_ub, clow, chigh, pollutant) = AQI_FORMULA_PARAMS[i]
            break
    aqi = ((iaqi_ub - iaqi_lb) / (chigh - clow)) * (ppm - clow) + iaqi_lb

    return aqi
    
def rc_time (pin_to_circuit):
    count = 0
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    time.sleep(0.1)
    GPIO.setup(pin_to_circuit, GPIO.IN)
    while (GPIO.input(pin_to_circuit) == GPIO.LOW):
        count += 1
    return count

  
while True:
    humidity, temperature = Adafruit_DHT.read_retry(dht_sensor, DHT_SENSOR_PIN)
    Humidity='{0:0.1f}% '.format(humidity)
    t=float(temperature)
    Temp='{0:0.1f}'.format(t)
    Temperature=Temp+'°C'
    
    
    gas_percentage = read_gas_percentage()
    Gas_Percentage= '{0:0.2f}'.format(gas_percentage)
    if float(Gas_Percentage) <=0.1:
            GPIO.output(buzzer_pin, GPIO.HIGH)
            time.sleep(10)
            GPIO.output(buzzer_pin, GPIO.LOW)
    else:
            GPIO.output(buzzer_pin, GPIO.LOW)
    time.sleep(2)
        
   
    
    if __name__ == '__main__':
        heat_sensor()
        
        value = read_sensor()
        aqi = calculate_aqi(value)
        Gas_concentration=" {:.2f} ppm".format(value)
        AQI= "{:.2f}".format(aqi)
        if float(AQI)>50:
                GPIO.output(buzzer_pin, GPIO.HIGH)
                time.sleep(10)
                GPIO.output(buzzer_pin, GPIO.LOW)
        else:
                GPIO.output(buzzer_pin, GPIO.LOW)
                
    LDR = rc_time(pin_to_circuit)
    
    if humidity is not None and temperature is not None and gas_percentage is not None and aqi is not None :
        row = [Temperature, Humidity, Gas_Percentage,AQI,Gas_concentration,LDR]   
        sheet.append_row(row)
    
    
    if temperature is not None:
        if t >=temp_threshold:
            GPIO.output(fan, GPIO.HIGH)
            time.sleep(100)
        else:
            GPIO.output(fan, GPIO.LOW)
        


