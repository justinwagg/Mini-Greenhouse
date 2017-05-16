#!/usr/bin/python
import threading
import pigpio
import datetime
import time
from datetime import timedelta
from password import *
import Adafruit_DHT
import sys
import mysql.connector
import logging
import os
from meteocalc import Temp, dew_point, heat_index

info = logging.getLogger(__name__).info
logging.basicConfig(level=logging.INFO,
                        filename='greenhouse.log', # log to this file
                        format='%(asctime)s %(message)s')

conn = mysql.connector.connect(user=user, password=password, host=host)
c = conn.cursor()

info('Started')

#dht sensor
sensor = Adafruit_DHT.DHT22
DHT_in = 4
DHT_out = 10

#GPIO settings
lights = 23
pi = pigpio.pi()
pi.set_mode(lights, pigpio.OUTPUT)
currentLight = 0
changeTime = datetime.datetime.now()

fan_power = 26
fan_control = 19
# pi.write(fan_power, 1)
# pi.write(fan_control, 1)


def FADE(current, target):
    if target > current:
        #fade up
        for i in range(current, target +1):
            # print('fading up, i = {}').format(i)
            pi.set_PWM_dutycycle(lights, i)
            time.sleep(.01)
            # time.sleep(.98**i)

    elif target < current:
        #fade down
        for i in range(current, target -1, -1):
            # print('fading down, i = {}').format(i)
            pi.set_PWM_dutycycle(lights, i)
            time.sleep(.03)
            # time.sleep(.98**i)

    return target, datetime.datetime.now()

def getLightStatus():
    q = 'select status from greenhouse.light_enable where id = (select max(id) from greenhouse.light_enable);'
    c.execute(q)
    result = c.fetchall()[0][0]
    #test
    return int(result)

def brightness(hour):

    y = 0.025*hour**4 - 1.2631*hour**3 + 18.507*hour**2 - 62.649*hour + 28.336
    # y = 0.0106*hour**4 - 0.6428*hour**3 + 10.512*hour**2 - 30.407*hour + 6.2322

    if y < 0 or hour == 0:
        y = 0
    elif y > 255:
        y = 255
    else:
        y
    # if 1 == 0:
    if getLightStatus() == 0:
        y = 0
    else:
        pass

    return int(y)

def dht_read(prior_dht_sql):
    # info("Running DHT Function")
    read_time = datetime.datetime.now()
    humidity_in, temperature_in = Adafruit_DHT.read_retry(sensor, DHT_in)
    info("Humidity In: {}, Temp In: {}".format(humidity_in, temperature_in))
    try:
        dew_in = dew_point(temperature=Temp(temperature_in, 'c'), humidity=humidity_in).f
    except ValueError:
        info("Dew In Exception")
        humidity_in, temperature_in = Adafruit_DHT.read_retry(sensor, DHT_in)
        dew_in = dew_point(temperature=Temp(temperature_in, 'c'), humidity=humidity_in).f

    q_in = "insert into greenhouse.dht_sensor (read_time, location, temperature_f, humidity, dew_point) VALUES ('{}','in', {},{},{});".format(read_time, temperature_in*1.8+32, humidity_in, dew_in)
    humidity_out, temperature_out = Adafruit_DHT.read_retry(sensor, DHT_out)
    info("Humidity Out: {}, Temp Out: {}".format(humidity_out, temperature_out))

    try:
        dew_out = dew_point(temperature=Temp(temperature_out, 'c'), humidity=humidity_out).f
    except ValueError:
        info("Dew Out Exception")
        humidity_out, temperature_out = Adafruit_DHT.read_retry(sensor, DHT_out)
        dew_out = dew_point(temperature=Temp(temperature_out, 'c'), humidity=humidity_out).f

    q_out = "insert into greenhouse.dht_sensor (read_time, location, temperature_f, humidity, dew_point) VALUES ('{}','out', {},{},{});".format(read_time, temperature_out*1.8+32, humidity_out, dew_out)
    #insert temperature stats into sql greenhouse database once an hour
    if ((read_time - prior_dht_sql).seconds >= 3600):
        c.execute(q_in)
        c.execute(q_out)
        conn.commit()
        inserted_sql = True
        info("Inserted into greenhouse.dht_sensor.")
    else:
        inserted_sql = False

    return inserted_sql, humidity_in, temperature_in*1.8+32, dew_in, read_time

def picture():
    now = datetime.datetime.now()
    tail = now.strftime('%Y%m%d_%H%M%S')
    tail2 = 'raspistill -awb sun -o /home/pi/Greenhouse/pictures/' + tail + '.jpg'
    info('Hit picture function.')
    os.system(tail2)

def fan_control(t_in, d_in, r_time):
    dew_rate = d_in / t_in
    dew_check = dew_rate > .85
    q = "insert into greenhouse.fan_check (read_time, fan_status, temp_in, dew_in, dew_ratio) VALUES ('{}',{},{},{},{});".format(r_time, dew_check, round(t_in,2), round(d_in,2), round(dew_rate,2))
    c.execute(q)
    conn.commit()
    # if prior_dew_check != dew_check:
    #     # print('no pass, insert state change')
    #     prior_dew_check = dew_check
    # else:
    #     pass


try:
    currentLight = pi.get_PWM_dutycycle(lights)
except pigpio.error:
    pass


now_ = datetime.datetime.now()
#subtract 6 hours to fool loop into inserting data on first loop
previous_dht = now_ - timedelta(hours=6)
previous_dht_sql = now_ - timedelta(hours=6)
previous_picture = now_.hour
prior_dew_check = False

try:
    while True:
        currentTime = datetime.datetime.now()
        currentLight, changeTime = FADE(currentLight, brightness(datetime.datetime.now().hour))

        #Do pictures once an hour, on the hour while the light is on
        if previous_picture != currentTime.hour:
            previous_picture = currentTime.hour      
            if currentLight > 0:
                picture()
            else:
                pass
                info("Light too low")
                info(currentLight)
        else:
            pass

        #Run DHT function every X seconds
        if (currentTime - previous_dht).seconds >= 15:
            #run DHT function, and capture whether or not an insert took place
            inserted_sql, humidity_in, temperature_in, dew_in, read_time = dht_read(previous_dht_sql)

            #Check most recent DHT readings against the fan settings
            fan_control(temperature_in, dew_in, read_time)

            if inserted_sql == True:
                previous_dht_sql = currentTime
            else:
                pass
            previous_dht = currentTime
        else:
            pass





except:
    info("Exception, quitting")
    logging.exception("Error")
    pi.write(lights, 0)
    # pi.write(fan_power, 0)
    # pi.write(fan_control, 0)
    pi.stop()
    sys.exit()
