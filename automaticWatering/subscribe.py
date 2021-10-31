import paho.mqtt.client as mqtt
import time

def on_message(client, userdata, message):
    topic = message.topic
    print("Received message: ", str(message.payload.decode("utf-8")))

client = mqtt.Client("Control")
client.on_message = on_message

client.connect("localhost")
client.loop_start()
client.subscribe("test/hum")

while True:
    time.sleep(1)

client.loop_stop()