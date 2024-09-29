""" Logic for creating and publishing own requests. """

from . import crud, schemas, models

from sqlalchemy.orm import Session
from datetime import datetime
import requests as req
import uuid6

import os


PUBLISHER_HOST=os.getenv("PUBLISHER_HOST")
PUBLISHER_PORT=os.getenv("PUBLISHER_PORT")

GROUP_ID=os.getenv("GROUP_ID")

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
    return crud.upsert_request(db, request, user_id=user_id, group_id=GROUP_ID)

def publish_request(request: schemas.Request):
    """Publish a request."""
    # Publish the request to the broker
    url = f"http://{PUBLISHER_HOST}:{PUBLISHER_PORT}/"
    response = req.post(url, json=request.model_dump_json())
    if response.status_code != 201:
        raise Exception(f"Failed to publish request: {response.text}")
    return response.json()