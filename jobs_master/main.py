"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=W0613

import logging
import os
import sys

import paho.mqtt.publish as publish
from fastapi import FastAPI

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()

logging.basicConfig(level=logging.INFO)

# Credentials for Jobs Broker
HOST = os.getenv("JOBS_HOST")
PORT = os.getenv("JOBS_PORT")
USER = os.getenv("JOBS_USER")
PASS = os.getenv("JOBS_PASSWORD")

if not HOST:
    logging.error("HOST environment variable not set")
    sys.exit(1)

if PORT and PORT.isdigit():
    PORT = int(PORT)
else:
    logging.error("PORT environment variable not set or not an integer")
    sys.exit(1)

app = FastAPI()

@app.get("/job/{id}")
async def get_job(id: int):
    return {"message": f"job id: {id}"}

@app.post("/job")
async def publish_message():
    return {"message": "job published"}

@app.get("/heartbeat")
async def heartbeat():
    return True
