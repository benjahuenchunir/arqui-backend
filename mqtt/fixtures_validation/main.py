"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=W0613

import json
import os
import logging
import sys

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

import paho.mqtt.client as mqtt
import paho.mqtt.enums as mqtt_enums
import requests

logging.basicConfig(level=logging.INFO)

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
USER = os.getenv("USER")
PASS = os.getenv("PASSWORD")

POST_TOKEN = os.getenv("POST_TOKEN")

API_HOST = os.getenv("API_HOST")
API_PORT = os.getenv("API_PORT")
API_PATH = os.getenv("VALIDATION_PATH")

if not HOST:
    logging.error("HOST environment variable not set")
    sys.exit(1)

if PORT and PORT.isdigit():
    PORT = int(PORT)
else:
    logging.error("PORT environment variable not set or not an integer")
    sys.exit(1)

if not API_HOST:
    logging.error("API_HOST environment variable not set")
    sys.exit(1)

if API_PORT and API_PORT.isdigit():
    API_PORT = int(API_PORT)
else:
    logging.error("API_PORT environment variable not set or not an integer")
    sys.exit(1)


def on_connect(client, userdata, flags, reason_code, properties):
    """Callback for when the client receives a CONNACK response from the server."""
    logging.info("Connected with result code %s", str(reason_code))
    client.subscribe(os.getenv("TOPIC"))


def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    payload = json.loads(json.loads(msg.payload.decode("utf-8")))

    try:
      requests.post(
          f"http://{API_HOST}:{API_PORT}/{API_PATH}",
          json=payload,
          headers={"Authorization": f"Bearer {POST_TOKEN}"},
          timeout=5,
      )
    except requests.exceptions.RequestException as e:
        logging.error("Error posting request: %s", str(e))
    logging.info("Request processed")

mqttc = mqtt.Client(mqtt_enums.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.username_pw_set(USER, PASS)
mqttc.connect(HOST, PORT, 60)

mqttc.loop_forever()
