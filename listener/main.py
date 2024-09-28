"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=W0613

import os
if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()
import logging
import sys
import logging
import paho.mqtt.client as mqtt
import paho.mqtt.enums as mqtt_enums
import json
from callbacks import on_history, on_info, on_validation

logging.basicConfig(level=logging.INFO)

HOST = os.getenv("MQTT_HOST")
PORT = os.getenv("MQTT_PORT")
USER = os.getenv("MQTT_USER")
PASS = os.getenv("MQTT_PASSWORD")
POST_TOKEN = os.getenv("POST_TOKEN")

if not HOST:
    logging.error("HOST environment variable not set")
    sys.exit(1)

if PORT and PORT.isdigit():
    PORT = int(PORT)
else:
    logging.error("PORT environment variable not set or not an integer")
    sys.exit(1)

if not POST_TOKEN:
    logging.error("POST_TOKEN environment variable not set")
    sys.exit(1)

TOPICS = {
    "info": on_info,
    "history": on_history,
    "validation": on_validation,
}

def on_connect(client, userdata, flags, reason_code, properties):
    """Callback for when the client receives a CONNACK response from the server."""
    logging.info("Connected to Broker with result code %s", str(reason_code))
    for topic in TOPICS:
        client.subscribe(topic)

def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    payload = json.loads(json.loads(msg.payload.decode("utf-8")))
    if msg.topic in TOPICS:
        TOPICS[msg.topic](payload)
    else:
        logging.error("No callback for topic %s", msg.topic)

mqttc = mqtt.Client(mqtt_enums.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.username_pw_set(USER, PASS )
mqttc.connect(HOST, PORT, 60)

mqttc.loop_forever()