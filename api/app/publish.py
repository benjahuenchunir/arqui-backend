""" Logic for publishing requests. """

from . import crud, schemas

from sqlalchemy.orm import Session
from datetime import datetime
import requests as req
import uuid6

import os

PUBLISHER_HOST=os.getenv("PUBLISHER_HOST")
PUBLISHER_PORT=os.getenv("PUBLISHER_PORT")

GROUP_ID=os.getenv("GROUP_ID")

POST_TOKEN=os.getenv("POST_TOKEN")

def create_request(db: Session, fixture_id: int, result: str, quantity: int, user_id: int):
    """Create a request."""
    db_fixture = crud.get_fixture_by_id(db, fixture_id)
    if db_fixture is None:
        return None
    request = schemas.Request(
        id=uuid6.uuid6(),
        group_id=GROUP_ID,
        fixture_id=fixture_id,
        league_name=db_fixture.league.name,
        round=db_fixture.league.round,
        date=db_fixture.date,
        result=result,
        deposit_token="",
        datetime=datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S UTC"),
        quantity=quantity,
        seller=0
    )
    publish_request(request)    
    return crud.upsert_request(db, request, user_id=user_id, group_id=GROUP_ID)

def publish_request(request: schemas.Request):
    """Publish a request."""
    # Publish the request to the broker
    url = f"http://{PUBLISHER_HOST}:{PUBLISHER_PORT}/"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {POST_TOKEN}"}
    response = req.post(url, data=request.model_dump_json(), headers=headers)
    if response.status_code != 201:
        raise Exception(f"Failed to publish request: {response.text}")
    return response.json()
