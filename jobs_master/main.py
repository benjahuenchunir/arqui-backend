"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=missing-docstring

import logging
import os
from contextlib import asynccontextmanager

import pika
import pika.adapters.blocking_connection
import pika.exceptions
from fastapi import FastAPI

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()

logging.basicConfig(level=logging.INFO)

# Credentials for Jobs Broker
USER = os.getenv("JOBS_USER")
PASS = os.getenv("JOBS_PASSWORD")

channels: list[pika.adapters.blocking_connection.BlockingChannel] = []


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not USER or not PASS:
        raise ValueError("JOBS_USER or JOBS_PASSWORD environment variables not set")

    credentials = pika.PlainCredentials(USER, PASS)
    params = pika.ConnectionParameters(host="rabbitmq", credentials=credentials)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="hello")
    channels.append(channel)
    logging.info("Connected to RabbitMQ!")

    yield

    connection.close()
    logging.info("Connection to RabbitMQ closed")


app = FastAPI(lifespan=lifespan)


@app.get("/job/{id}")
async def get_job(_id: int):
    return {"message": f"job id: {_id}"}


@app.post("/job")
async def publish_message():
    return {"message": "job published"}


@app.get("/heartbeat")
async def heartbeat():
    channels[0].basic_publish(exchange="", routing_key="hello", body="Hello World!")
    print(" [x] Sent 'Hello World!'")
