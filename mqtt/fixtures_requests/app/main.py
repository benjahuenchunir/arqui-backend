from fastapi import Depends, FastAPI, HTTPException, Request, status
import paho.mqtt.publish as publish
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import requests
import logging
import sys

import os

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

app = FastAPI()

class Msg(BaseModel):
    data: str

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
USER = os.getenv("USER")
PASS = os.getenv("PASSWORD")

POST_TOKEN = os.getenv("POST_TOKEN")

TOPIC = os.getenv("TOPIC")

API_HOST = os.getenv("API_HOST")
API_PORT = os.getenv("API_PORT")
API_PATH = os.getenv("API_PATH")

PUBLISH_PATH=os.getenv("PUBLISH_REQUESTS_PATH")
RECIEVE_PATH=os.getenv("RECIEVE_REQUESTS_PATH")

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


@app.post(f"/{PUBLISH_PATH}")
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



@app.post(f"/{RECIEVE_PATH}")
async def recieve(
    request: Msg,
    token: None = Depends(verify_post_token)
    ):
    mesage = request.data
    try:
        response = requests.post(f"http://{API_HOST}:{API_PORT}/{API_PATH}",
                                json={
                                    "headers": {"Authorization": f"Bearer {POST_TOKEN}"},
                                    "timeout": 5,
                                    "data": mesage
                                    }
                                )
        return JSONResponse(status=response.status_code, content=response.json())
    except Exception as e:
        return JSONResponse(status=500, content={"error": str(e)})