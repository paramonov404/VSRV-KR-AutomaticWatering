import paho.mqtt.client as mqtt
from random import uniform
import time

def on_log(client, userdata, level, buf):
    print("log: " + buf)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected OK.")
    else:
        print("Bad connection. Returned code: ", rc)

def on_disconnect(client, userdata, flags, rc=0):
    print("Disconnected result code: " + str(rc))

client = mqtt.Client("Humidity_sensor")
client.on_connect=on_connect
client.on_disconnect=on_disconnect
#client.on_log=on_log

client.connect("localhost")
client.loop_start()
while True:
  randNumber = round(uniform(20, 40), 2)
  client.publish("test/hum", randNumber)
  print("Just published " + str(randNumber) + " to topic test/hum.")
  time.sleep(1)
client.loop_stop()
client.disconnect()