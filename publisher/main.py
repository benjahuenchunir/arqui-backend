"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=W0613

import os
import logging
import sys
from fastapi import Depends, FastAPI, HTTPException, Request
import paho.mqtt.publish as publish
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import logging

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
    data: str

def verify_post_token(request: Request, post_token: str):
    """Verify the POST token."""
    token = request.headers.get("Authorization")
    if token != f"Bearer {post_token}":
        raise HTTPException(status_code=403, detail="Forbidden")

app = FastAPI()

@app.get("/")
async def root():
    """Root endpoint. Just to show example API-PUBLISHER connection."""
    return {"message": "Publisher is running"}

@app.post("/")
async def publish_message(
    request: Msg,
    token: None = Depends(lambda req: verify_post_token(req, POST_TOKEN))
):
    message = request.data
    try:
        publish.single(
            "fixtures/requests", 
            message, 
            hostname=HOST,
            port=PORT,
            auth={
                "username": USER,
                "password": PASS
            }
        )
        return JSONResponse(status_code=200, content={"message": "Message published successfully"})
    except Exception as e:
        logging.error("Error publishing message: %s", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
