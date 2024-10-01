""" Logic for publishing requests. """

import os
import uuid
from datetime import datetime, timezone

import requests
from requests.exceptions import RequestException
from sqlalchemy.orm import Session

from . import broker_schema, crud, schemas

PUBLISHER_HOST = os.getenv("PUBLISHER_HOST")
PUBLISHER_PORT = os.getenv("PUBLISHER_PORT")

GROUP_ID = os.getenv("GROUP_ID")

POST_TOKEN = os.getenv("POST_TOKEN")


def create_request(db: Session, req: schemas.FrontendRequest):
    """Create a request."""
    db_fixture = crud.get_fixture_by_id(db, req.fixture_id)

    if db_fixture is None:
        return None

    request = broker_schema.Request(
        request_id=uuid.uuid4(),
        group_id=str(GROUP_ID),
        fixture_id=req.fixture_id,
        league_name=db_fixture.league.name,
        round=db_fixture.league.round,
        date=db_fixture.date,  # type: ignore
        result=req.result,
        datetime=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S UTC"),
        quantity=req.quantity,
    )
    publish_request(request)

    return request


def publish_request(request: broker_schema.Request):
    """Publish a request."""
    # Publish the request to the broker
    url = f"http://{PUBLISHER_HOST}:{PUBLISHER_PORT}/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {POST_TOKEN}",
    }
    response = requests.post(
        url,
        json={"payload": request.model_dump_json()},
        headers=headers,
        timeout=30,
    )
    if response.status_code != 200:
        raise RequestException(response.text)
