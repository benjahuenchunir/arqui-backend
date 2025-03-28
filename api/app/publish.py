""" Logic for publishing requests. """

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import requests as http_requests
from app.crud import fixtures, requests, users
from app.schemas import request_schemas, response_schemas
from fastapi import HTTPException
from requests.exceptions import RequestException
from sqlalchemy.orm import Session

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

    db_fixture = fixtures.get_fixture_by_id(db, req.fixture_id)

    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    db_user = users.get_user(db, req.uid)

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    published_request = response_schemas.Request(
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
        seller=0 if not bool(db_user.admin) else int(GROUP_ID) if GROUP_ID else 2,
    )

    publish_request(published_request)

    return published_request


def publish_request(request: response_schemas.Request):
    """Publish a request."""
    # Publish the request to the broker
    url = f"http://{PUBLISHER_HOST}:{PUBLISHER_PORT}/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {POST_TOKEN}",
    }
    response = http_requests.post(
        url,
        json={"payload": request.model_dump_json()},
        headers=headers,
        timeout=30,
    )
    if response.status_code != 200:
        raise RequestException(response.text)


def create_validation(db: Session, req: request_schemas.RequestValidation):
    """Create a request validation."""
    db_request = requests.get_request_by_id(db, req.request_id)  # type: ignore

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
    response = http_requests.post(
        url,
        json={"payload": request.model_dump_json()},
        headers=headers,
        timeout=30,
    )
    if response.status_code != 200:
        raise RequestException(response.text)


def create_offer(db: Session, offer: request_schemas.OfferShort):
    """Create and publish an offer."""

    db_fixture = fixtures.get_fixture_by_id(db, offer.fixture_id)

    if db_fixture is None:
        return None

    match offer.result:
        case db_fixture.home_team.team.name:
            if offer.quantity > db_fixture.reserved_home:  # type: ignore
                return None
        case db_fixture.away_team.team.name:
            if offer.quantity > db_fixture.reserved_away:  # type: ignore
                return None
        case "---":
            if offer.quantity > db_fixture.reserved_draw:  # type: ignore
                return None

    publish_offer = response_schemas.Auction(
        auction_id=uuid.uuid4(),
        proposal_id="",
        fixture_id=offer.fixture_id,
        league_name=db_fixture.league.name,
        round=db_fixture.league.round,
        result=offer.result,
        quantity=offer.quantity,
        group_id=int(GROUP_ID) if GROUP_ID else 2,
        type="offer",
    )

    publish_auction(publish_offer)

    return publish_offer


def create_proposal(db: Session, proposal: request_schemas.ProposalShort):
    """Create and publish a proposal."""

    db_fixture = fixtures.get_fixture_by_id(db, proposal.fixture_id)

    if db_fixture is None:
        return None

    match proposal.result:
        case db_fixture.home_team.team.name:
            if proposal.quantity > db_fixture.reserved_home:  # type: ignore
                return None
        case db_fixture.away_team.team.name:
            if proposal.quantity > db_fixture.reserved_away:  # type: ignore
                return None
        case "---":
            if proposal.quantity > db_fixture.reserved_draw:  # type: ignore
                return None

    published_proposal = response_schemas.Auction(
        auction_id=proposal.auction_id,
        proposal_id=uuid.uuid4(),
        fixture_id=proposal.fixture_id,
        league_name=db_fixture.league.name,
        round=db_fixture.league.round,
        result=proposal.result,
        quantity=proposal.quantity,
        group_id=int(GROUP_ID) if GROUP_ID else 2,
        type="proposal",
    )

    publish_auction(published_proposal)

    return published_proposal


def create_acceptance(proposal: request_schemas.Proposal):
    """Accept a proposal."""

    published_proposal = response_schemas.Auction(
        auction_id=proposal.auction_id,
        proposal_id=proposal.proposal_id,
        fixture_id=proposal.fixture_id,
        league_name=proposal.league_name,
        round=proposal.round,
        result=proposal.result,
        quantity=proposal.quantity,
        group_id=proposal.group_id,
        type="acceptance",
    )

    publish_auction(published_proposal)

    return published_proposal


def create_rejection(proposal: request_schemas.Proposal):
    """Reject a proposal."""

    published_proposal = response_schemas.Auction(
        auction_id=proposal.auction_id,
        proposal_id=proposal.proposal_id,
        fixture_id=proposal.fixture_id,
        league_name=proposal.league_name,
        round=proposal.round,
        result=proposal.result,
        quantity=proposal.quantity,
        group_id=proposal.group_id,
        type="rejection",
    )

    publish_auction(published_proposal)

    return published_proposal


def publish_auction(auction: response_schemas.Auction):
    """Publish an auction."""
    # Publish the auction to the broker
    url = f"http://{PUBLISHER_HOST}:{PUBLISHER_PORT}/auction"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {POST_TOKEN}",
    }
    response = http_requests.post(
        url,
        json={"payload": auction.model_dump_json()},
        headers=headers,
        timeout=30,
    )
    if response.status_code != 200:
        raise RequestException(response.text)
