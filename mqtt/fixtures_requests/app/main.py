from fastapi import Depends, FastAPI, HTTPException, Request, status
import paho.mqtt.publish as publish
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import requests
import logging
import sys

import os

app = FastAPI()

class Msg(BaseModel):
    data: str

POST_TOKEN = os.getenv("POST_TOKEN")

TOPIC = os.getenv("TOPIC")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
USER = os.getenv("USER")
PASS = os.getenv("PASSWORD")

if not HOST:
    logging.error("HOST environment variable not set")
    sys.exit(1)

if PORT and PORT.isdigit():
    PORT = int(PORT)
else:
    logging.error("PORT environment variable not set or not an integer")
    sys.exit(1)

def verify_post_token(request: Request):
    """Verify the POST token."""
    token = request.headers.get("Authorization")
    if token != f"Bearer {POST_TOKEN}":
        raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/publish")
async def publish(
    request: Msg,
    token: None = Depends(verify_post_token)
    ):
    mesage = request.data
    try:
        publish.single(
            TOPIC, 
            mesage, 
            hostname=HOST,
            port=PORT,
            auth={
                "username": USER,
                "password": PASS
            }
            )
        return JSONResponse(status=200)
    except Exception as e:
        return JSONResponse(status=500, content={"error": str(e)})

API_URL = os.getenv("API_URL")

@app.post("/receive")
async def recieve(
    request: Msg,
    token: None = Depends(verify_post_token)
    ):
    mesage = request.data
    try:
        response = requests.post(API_URL, json={
            "headers": {"Authorization": f"Bearer {POST_TOKEN}"},
            "timeout": 5,
            "data": mesage
            })
        return JSONResponse(status=response.status_code, content=response.json())
    except Exception as e:
        return JSONResponse(status=500, content={"error": str(e)})