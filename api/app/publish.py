""" Logic for publishing requests. """

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import requests
from requests.exceptions import RequestException
from sqlalchemy.orm import Session

from . import crud
from .schemas import request_schemas, response_schemas

PUBLISHER_HOST = os.getenv("PUBLISHER_HOST")
PUBLISHER_PORT = os.getenv("PUBLISHER_PORT")

GROUP_ID = os.getenv("GROUP_ID")

POST_TOKEN = os.getenv("POST_TOKEN")


def create_request(
    db: Session,
    req: request_schemas.RequestShort,
    deposit_token: str = "",
    request_id: Optional[str] = None,
):
    """Create a request."""
    db_fixture = crud.get_fixture_by_id(db, req.fixture_id)

    if db_fixture is None:
        return None

    request = response_schemas.Request(
        request_id=request_id or uuid.uuid4(),  # type: ignore
        group_id=str(GROUP_ID),
        fixture_id=req.fixture_id,
        league_name=db_fixture.league.name,
        round=db_fixture.league.round,
        date=db_fixture.date,  # type: ignore
        result=req.result,
        deposit_token=deposit_token,
        datetime=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S UTC"),
        quantity=req.quantity,
        wallet=not bool(deposit_token),
        seller=0,
    )
    publish_request(request)

    return request


def publish_request(request: response_schemas.Request):
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


def create_validation(db: Session, req: request_schemas.RequestValidation):
    """Create a request validation."""
    db_request = crud.get_request_by_id(db, req.request_id)  # type: ignore

    if db_request is None:
        return None

    request = response_schemas.RequestValidation(
        request_id=req.request_id,  # type: ignore
        group_id=str(GROUP_ID),
        seller=req.seller,
        valid=req.valid,
    )

    publish_validation(request)

    return request


def publish_validation(request: response_schemas.RequestValidation):
    """Publish a request validation."""
    # Publish the request to the broker
    url = f"http://{PUBLISHER_HOST}:{PUBLISHER_PORT}/validate"
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
