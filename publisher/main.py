"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=W0613

import logging
import os
import sys

import paho.mqtt.publish as publish
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()

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


class Msg(BaseModel):
    payload: str


def verify_post_token(request: Request):
    """Verify the POST token."""
    token = request.headers.get("Authorization")
    if token != f"Bearer {POST_TOKEN}":
        raise HTTPException(status_code=403, detail="Forbidden")


app = FastAPI()


@app.get("/")
async def root():
    """Root endpoint. Just to show example API-PUBLISHER connection."""
    return {"message": "Publisher is running"}


@app.post("/")
async def publish_message(
    request: Msg,
    status_code=status.HTTP_200_OK,
    token: None = Depends(verify_post_token),
):
    """Publish a message to the MQTT broker."""
    message = request.payload
    try:
        publish.single(
            "fixtures/requests",
            payload=message,
            hostname=HOST,  # type: ignore
            port=PORT,  # type: ignore
            auth={"username": USER, "password": PASS},  # type: ignore
        )
    except Exception as e:
        logging.error(f"Failed to publish message: {e}")
        return JSONResponse(
            status_code=500, content={"message": "Failed to publish message"}
        )


@app.post("/validate")
async def publish_validation(
    request: Msg,
    status_code=status.HTTP_200_OK,
    token: None = Depends(verify_post_token),
):
    """Publish a validation to the MQTT broker."""
    message = request.payload
    try:
        publish.single(
            "fixtures/validation",
            payload=message,
            hostname=HOST,  # type: ignore
            port=PORT,  # type: ignore
            auth={"username": USER, "password": PASS},  # type: ignore
        )
    except Exception as e:
        logging.error(f"Failed to publish message: {e}")
        return JSONResponse(
            status_code=500, content={"message": "Failed to publish message"}
        )
