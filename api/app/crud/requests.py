"""CRUD operations for requests."""

import asyncio
import os
import uuid
from datetime import datetime

import requests
from app.crud import fixtures, users
from app.lambda_client import invocar_generar_boleta
from app.routers.requests import notify_clients
from app.schemas import request_schemas
from app.schemas.response_schemas import RequestShort
from sqlalchemy import desc
from sqlalchemy.orm import Session

from db import models

BET_PRICE = int(os.getenv("BET_PRICE"))
GROUP_ID = os.getenv("GROUP_ID")


def reserve_request(
    db: Session,
    request: request_schemas.RequestShort,
    bets: str,
):
    """Create a request via reserved bets. (no validation needed)"""

    db_fixture = fixtures.get_fixture_by_id(db, request.fixture_id)

    if db_fixture is None:
        return None

    db_request = models.RequestModel(
        request_id=str(uuid.uuid4()),
        group_id=2,
        fixture_id=request.fixture_id,
        league_name=db_fixture.league.name,
        round=db_fixture.league.round,
        date=datetime.now(),
        result=request.result,
        datetime=str(datetime.timestamp(datetime.now())),
        quantity=request.quantity,
        wallet=True,
        seller=0,
        status=models.RequestStatusEnum.APPROVED,
        user_id=request.uid,
    )
    db.add(db_request)

    match bets:
        case "Home":
            db_fixture.reserved_home -= request.quantity  # type: ignore
        case "Away":
            db_fixture.reserved_away -= request.quantity  # type: ignore
        case "Draw":
            db_fixture.reserved_draw -= request.quantity  # type: ignore
        case _:
            return None

    db.commit()
    db.refresh(db_fixture)

    # Notify connected clients
    print("User id in upsert is ", str(db_request.user_id))
    db_requests = get_requests(db, str(db_request.user_id))
    notify_clients(str(db_request.user_id), db_requests)

    return db_request


def upsert_request(
    db: Session,
    request: request_schemas.Request,
    wallet: bool = False,
):
    """Create a new request."""

    db_fixture = fixtures.get_fixture_by_id(db, request.fixture_id)

    if db_fixture is None:
        return None

    print("Upser request", request)

    db_request: models.RequestModel = models.RequestModel(
        request_id=str(request.request_id),
        group_id=int(request.group_id),
        fixture_id=int(request.fixture_id),
        league_name=request.league_name,
        round=request.round,
        date=request.date,
        result=request.result,
        deposit_token=request.deposit_token,
        datetime=request.datetime,
        quantity=request.quantity,
        wallet=wallet,
        seller=request.seller,
        status=models.RequestStatusEnum.PENDING,
    )
    db.add(db_request)

    db_fixture.remaining_bets -= request.quantity  # type: ignore

    if request.seller == 2:
        match request.result:
            case db_fixture.home_team.team.name:
                db_fixture.reserved_home += request.quantity  # type: ignore
            case db_fixture.away_team.team.name:
                db_fixture.reserved_away += request.quantity  # type: ignore
            case _:
                db_fixture.reserved_draw += request.quantity  # type: ignore

    db.commit()
    db.refresh(db_fixture)
    db.refresh(db_request)

    # Notify connected clients
    print("User id in upsert is ", str(db_request.user_id))
    db_requests = get_requests(db, str(db_request.user_id))
    notify_clients(str(db_request.user_id), db_requests)

    return db_request


async def update_request(
    db: Session, request_id: str, validation: request_schemas.RequestValidation
):
    """Update a request."""

    # if type(validation.group_id) != int:
    #     try:
    #         validation.group_id = int(validation.group_id)
    #     except ValueError:
    #         validation.group_id = 0

    # validation.request_id = str(validation.request_id)

    db_request = (
        db.query(models.RequestModel)
        .filter(models.RequestModel.request_id == request_id)
        .one_or_none()
    )

    if db_request is None:
        return None

    if validation.valid:
        db_request.status = models.RequestStatusEnum.APPROVED  # type: ignore
        asyncio.create_task(assign_job(db, db_request.request_id))  # type: ignore
        print("Antes de generar boleta")
        asyncio.create_task(generate_ticket(db, db_request.request_id))  # type: ignore
    else:
        db_request.status = models.RequestStatusEnum.REJECTED  # type: ignore
        db_fixture = (
            db.query(models.FixtureModel).filter_by(id=db_request.fixture_id).one()
        )
        db_fixture.remaining_bets += db_request.quantity  # type: ignore
        asyncio.create_task(return_money(db, request_id))

    db.commit()
    db.refresh(db_request)

    # Notify connected clients
    print("User id in update is ", db_request.user_id)
    requests_notify = get_requests(db, db_request.user_id)
    notify_clients(db_request.user_id, requests_notify)

    return db_request


async def generate_ticket(db: Session, request_id: str):
    await asyncio.sleep(10)
    try:
        db_request = (
            db.query(models.RequestModel).filter_by(request_id=request_id).one_or_none()
        )
        if db_request is None:
            return None

        db_user = (
            db.query(models.UserModel).filter_by(id=db_request.user_id).one_or_none()
        )

        if db_user is None:
            return None

        url = invocar_generar_boleta(
            {
                "grupo": GROUP_ID,
                "usuario": db_user.email,
                "equipos": db_request.fixture.home_team.team.name
                + " vs "
                + db_request.fixture.away_team.team.name,
            }
        )
        print(url)
        db_request.url_boleta = url
        db.commit()
        db.refresh(db_request)
    except Exception as e:
        print("ERROR generando boleta", e)


async def assign_job(db: Session, request_id: str):
    """Assign a job to a user."""
    await asyncio.sleep(10)

    db_request = (
        db.query(models.RequestModel).filter_by(request_id=request_id).one_or_none()
    )

    if db_request is None:
        return None

    db_user = db.query(models.UserModel).filter_by(id=db_request.user_id).one_or_none()

    if db_user is None:
        return None

    url = "http://arquisis-jobs-master:7998/job"
    headers = {"Content-Type": "application/json"}
    user = {"user_id": db_user.id}
    job_id = requests.post(url, headers=headers, json=user).json()
    db_user.job_id = job_id["job_id"]  # type: ignore

    db.commit()
    db.refresh(db_user)
    return db_user


async def return_money(db: Session, request_id: str):
    """Return money for a rejected request."""
    await asyncio.sleep(5)
    db_request = (
        db.query(models.RequestModel)
        .filter(models.RequestModel.request_id == request_id)
        .one_or_none()
    )
    if db_request is None:
        return None

    db_user = db.query(models.UserModel).filter_by(id=db_request.user_id).one_or_none()
    if db_user is None:
        return None

    users.update_balance(db, db_user.id, db_request.quantity * BET_PRICE, add=True)  # type: ignore

    db.commit()
    db.refresh(db_request)
    db.refresh(db_user)
    return db_request


async def link_request(db: Session, link: request_schemas.Link):
    """Link a request to a user."""
    await asyncio.sleep(5)
    db_request = (
        db.query(models.RequestModel)
        .filter(models.RequestModel.request_id == link.request_id)
        .one_or_none()
    )
    if db_request is None:
        return None

    db_user = db.query(models.UserModel).filter_by(id=link.uid).one_or_none()
    if db_user is None:
        return None

    db_request.user = db_user
    db_request.location = link.location  # type: ignore

    db.commit()
    db.refresh(db_request)

    # Notify connected clients
    print("User id in link is ", db_request.user_id)
    requests_notify = get_requests(db, db_request.user_id)
    notify_clients(db_request.user_id, requests_notify)

    return db_request


def get_requests(db: Session, user_id: str):
    """Get requests by user ID, sorted by datetime."""
    requests = (
        db.query(models.RequestModel)
        .filter_by(user_id=user_id)
        .order_by(desc(models.RequestModel.datetime))
        .all()
    )
    return [RequestShort.model_validate(request) for request in requests]


def create_transaction(db: Session, transaction: request_schemas.RequestShort):
    """Create a new transaction."""
    db_transaction = models.TransactionModel(
        request_id=uuid.uuid4(),
        fixture_id=transaction.fixture_id,
        user_id=transaction.uid,
        quantity=transaction.quantity,
        result=transaction.result,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_transaction(db: Session, token: str):
    """Get transactions by user ID."""
    return db.query(models.TransactionModel).filter_by(token=token).one_or_none()


def get_request_by_id(db: Session, request_id: str):
    """Get request details by request ID."""
    return (
        db.query(models.RequestModel)
        .filter(models.RequestModel.request_id == request_id)
        .one_or_none()
    )
