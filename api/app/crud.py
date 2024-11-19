"""CRUD operations for the fixtures API."""

# pylint: disable=C0103

import asyncio
import os
import uuid
import warnings
from datetime import datetime
from typing import Optional

import requests
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import func

from db import models

from .schemas import request_schemas
from .lambda_client import invocar_generar_boleta
from .routers.requests import notify_clients

from .schemas.response_schemas import RequestShort
from sqlalchemy import desc

warnings.filterwarnings("ignore", category=SAWarning)

BET_PRICE = int(os.getenv("BET_PRICE"))
GROUP_ID = os.getenv("GROUP_ID")


def upsert_fixture(db: Session, fixture: request_schemas.WholeFixture):
    """Upsert a fixture."""

    # Upsert FixtureModel
    db_fixture = db.merge(
        models.FixtureModel(
            id=fixture.fixture.id,
            referee=fixture.fixture.referee,
            timezone=fixture.fixture.timezone,
            date=fixture.fixture.date,
            timestamp=fixture.fixture.timestamp,
            status_long=fixture.fixture.status.long,
            status_short=fixture.fixture.status.short,
            status_elapsed=fixture.fixture.status.elapsed,
            id_home_team=fixture.teams.home.id,
            id_away_team=fixture.teams.away.id,
            id_league=fixture.league.id,
        )
    )

    # Upsert LeagueModel
    db.merge(
        models.LeagueModel(
            id=fixture.league.id,
            name=fixture.league.name,
            country=fixture.league.country,
            logo_url=fixture.league.logo,
            flag_url=fixture.league.flag,
            season=fixture.league.season,
            round=fixture.league.round,
        )
    )

    # Upsert TeamModel for home team
    db.merge(
        models.TeamModel(
            id=fixture.teams.home.id,
            name=fixture.teams.home.name,
            logo_url=fixture.teams.home.logo,
        )
    )

    # Upsert TeamModel for away team
    db.merge(
        models.TeamModel(
            id=fixture.teams.away.id,
            name=fixture.teams.away.name,
            logo_url=fixture.teams.away.logo,
        )
    )

    # Upsert FixtureTeamModel for home team
    db_fixture_home_team = (
        db.query(models.FixtureTeamModel)
        .filter_by(id_fixture=fixture.fixture.id, id_team=fixture.teams.home.id)
        .first()
    )
    if db_fixture_home_team:
        db_fixture_home_team.goals = fixture.goals.home
    else:
        db_fixture_home_team = models.FixtureTeamModel(
            id_fixture=fixture.fixture.id,
            id_team=fixture.teams.home.id,
            goals=fixture.goals.home,
        )
        db.add(db_fixture_home_team)

    # Upsert FixtureTeamModel for away team
    db_fixture_away_team = (
        db.query(models.FixtureTeamModel)
        .filter_by(id_fixture=fixture.fixture.id, id_team=fixture.teams.away.id)
        .first()
    )
    if db_fixture_away_team:
        db_fixture_away_team.goals = fixture.goals.away
    else:
        db_fixture_away_team = models.FixtureTeamModel(
            id_fixture=fixture.fixture.id,
            id_team=fixture.teams.away.id,
            goals=fixture.goals.away,
        )
        db.add(db_fixture_away_team)

    # TODO if names of odds could change its better to delete all odds and reinsert them
    # Upsert OddModel and OddValueModel
    for odd in fixture.odds:
        # Since odds have same ids for different fixtures, we need to check if they exist
        db_odd = (
            db.query(models.OddModel)
            .filter_by(
                id_fixture=fixture.fixture.id,
                name=odd.name,  # This assumes that the name of the odd for a fixture is unique
            )
            .first()
        )

        if db_odd:
            pass  # Update any future fields here
        else:
            db_odd = models.OddModel(  # Autoincremented ID
                id_fixture=fixture.fixture.id, name=odd.name
            )
            db.add(db_odd)
            # For some reason without this commit the first insertion odd values are not saved
            db.commit()
            db.refresh(db_odd)

        for value in odd.values:
            # Since odd values do not have a unique ID, we need to check if they exist
            db_odd_value = (
                db.query(models.OddValueModel)
                .filter_by(id_odd=db_odd.id, bet=value.value)
                .first()
            )
            if db_odd_value:
                db_odd_value.value = float(value.odd)
            else:
                db_odd_value = models.OddValueModel(
                    id_odd=db_odd.id, value=float(value.odd), bet=value.value
                )
                db.add(db_odd_value)

    db.commit()
    db.refresh(db_fixture)

    return db_fixture


def update_fixture(
    db: Session,
    fixture_id: int,
    fixture: request_schemas.FixtureUpdate,
):
    """Update a fixture."""
    db_fixture = (
        db.query(models.FixtureModel)
        .filter(models.FixtureModel.id == fixture_id)
        .one_or_none()
    )
    if db_fixture is None:
        return None

    db_fixture.referee = fixture.fixture.referee
    db_fixture.timezone = fixture.fixture.timezone
    db_fixture.date = fixture.fixture.date
    db_fixture.timestamp = fixture.fixture.timestamp
    db_fixture.status_long = fixture.fixture.status.long
    db_fixture.status_short = fixture.fixture.status.short
    db_fixture.status_elapsed = fixture.fixture.status.elapsed

    db_fixture.home_team.goals = fixture.goals.home
    db_fixture.away_team.goals = fixture.goals.away
    db.commit()
    db.refresh(db_fixture)
    return db_fixture


def get_fixtures(
    db: Session,
    page: int = 0,
    count: int = 25,
    home: Optional[str] = None,
    away: Optional[str] = None,
    date: Optional[str] = None,
):
    """Get fixtures from the database."""
    HomeTeam = aliased(models.TeamModel)
    AwayTeam = aliased(models.TeamModel)

    query = (
        db.query(models.FixtureModel)
        .join(
            models.FixtureTeamModel,
            models.FixtureModel.id == models.FixtureTeamModel.id_fixture,
        )
        .join(HomeTeam, models.FixtureModel.id_home_team == HomeTeam.id)
        .join(AwayTeam, models.FixtureModel.id_away_team == AwayTeam.id)
    )

    date_obj = datetime.strptime(date, "%Y-%m-%d") if date else None

    if home:
        query = query.filter(HomeTeam.name == home)
    if away:
        query = query.filter(AwayTeam.name == away)
    if date:
        query = query.filter(func.date(models.FixtureModel.date) == date_obj)

    return (
        query.order_by(models.FixtureModel.date.desc())
        .offset(page * count)
        .limit(count)
        .all()
    )


def get_available_fixtures(
    db: Session,
    page: int = 0,
    count: int = 25,
):
    """Get available fixtures from the database."""

    query = (
        db.query(models.FixtureModel)
        .filter(models.FixtureModel.status_short == "NS")
        .filter(models.FixtureModel.remaining_bets > 0)
    )

    return query.offset(page * count).limit(count).all()


def get_fixture_by_id(db: Session, fixture_id: int):
    """Get fixture details by fixture ID."""
    return (
        db.query(models.FixtureModel)
        .filter(models.FixtureModel.id == fixture_id)
        .one_or_none()
    )


def upsert_request(
    db: Session,
    request: request_schemas.Request,
    wallet: bool = False,
):
    """Create a new request."""

    db_fixture = get_fixture_by_id(db, request.fixture_id)

    if db_fixture is None:
        return None

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

    # if request.group_id == group_id and user_id:
    #     db_user = db.query(models.UserModel).filter_by(id=user_id).one_or_none()
    #     if db_user:
    #         db_request.user = db_user
    #         update_balance(
    #             db, db_request.user.id, db_request.quantity * BET_PRICE, add=False
    #         )

    # db_request.fixture = db_fixture
    # db_fixture.remaining_bets -= request.quantity

    db.commit()
    db.refresh(db_fixture)
    db.refresh(db_request)
    
    # Notify connected clients
    print("User id in upsert is ", db_request.user_id)
    requests = get_requests(db, db_request.user_id)
    notify_clients(db_request.user_id, requests)
    
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
    requests = get_requests(db, db_request.user_id)
    notify_clients(db_request.user_id, requests)
    
    return db_request

async def generate_ticket(db: Session, request_id: str):
    await asyncio.sleep(10)
    try:
        db_request = (
        db.query(models.RequestModel).filter_by(request_id=request_id).one_or_none()
        )
        if db_request is None:
            return None
        
        db_user = db.query(models.UserModel).filter_by(id=db_request.user_id).one_or_none()

        if db_user is None:
            return None
    
        url = invocar_generar_boleta(
            {
                "grupo": GROUP_ID,
                "usuario": db_user.email,
                "equipos": db_request.fixture.home_team.team.name + " vs " + db_request.fixture.away_team.team.name,
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

    update_balance(db, db_user.id, db_request.quantity * BET_PRICE, add=True)  # type: ignore

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
    requests = get_requests(db, db_request.user_id)
    notify_clients(db_request.user_id, requests)
    
    return db_request


def create_user(db: Session, user: request_schemas.User):
    """Create a new user."""
    # Check if user already exists
    db_user = db.query(models.UserModel).filter_by(id=user.uid).one_or_none()

    if db_user:
        return db_user

    db_user = models.UserModel(
        id=user.uid,
        email=user.email,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: str):
    """Get user details by user ID."""
    return db.query(models.UserModel).filter_by(id=user_id).one_or_none()


def get_requests(db: Session, user_id: str):
    """Get requests by user ID, sorted by datetime."""
    requests = db.query(models.RequestModel).filter_by(user_id=user_id).order_by(desc(models.RequestModel.datetime)).all()
    return [RequestShort.model_validate(request) for request in requests]


def update_balance(db: Session, user_id: str, amount: float, add: bool = True):
    """Update user wallet."""
    db_user = db.query(models.UserModel).filter_by(id=user_id).one_or_none()
    if db_user is None:
        return None
    if add:
        db_user.wallet += amount  # type: ignore
    else:
        db_user.wallet -= amount  # type: ignore
    db.commit()
    db.refresh(db_user)
    return db_user


def get_request_by_id(db: Session, request_id: str):
    """Get request details by request ID."""
    return (
        db.query(models.RequestModel)
        .filter(models.RequestModel.request_id == request_id)
        .one_or_none()
    )


def pay_bets(db: Session, fixture_id: int):
    """Pay bets for a finished fixture."""

    print("Paying bets for fixture", fixture_id)

    db_fixture = get_fixture_by_id(db, fixture_id)

    if db_fixture is None:
        print("Fixture not found")
        return None

    db_requests = (
        db.query(models.RequestModel)
        .filter(models.RequestModel.fixture_id == fixture_id)
        .filter(models.RequestModel.status == models.RequestStatusEnum.APPROVED)
        .filter(models.RequestModel.group_id == 2)
        .all()
    )

    if not db_requests:
        print("No requests found")
        return None

    print("Found requests", db_requests)

    for db_request in db_requests:
        if db_request.paid:
            continue

        if not db_request.user_id:
            continue

        db_user = db.query(models.UserModel).filter_by(id=db_request.user_id).one()
        if db_request.result == db_fixture.home_team.team.name:
            mult = db_fixture.odds[0].values[0].value
        elif db_request.result == db_fixture.away_team.team.name:
            mult = db_fixture.odds[0].values[2].value
        else:
            mult = db_fixture.odds[0].values[1].value

        amount = db_request.quantity * mult * BET_PRICE

        if db_fixture.home_team.goals > db_fixture.away_team.goals:
            wwinner = db_fixture.home_team.team.name
        elif db_fixture.home_team.goals < db_fixture.away_team.goals:
            wwinner = db_fixture.away_team.team.name
        else:
            wwinner = "---"

        if wwinner == db_request.result:
            update_balance(db, db_user.id, amount, add=True)
            db_request.correct = True

        db_request.paid = True

    db.commit()
    return db_requests


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


def get_recommendations(db: Session, ids: list):
    """Get recommended fixtures."""
    return db.query(models.FixtureModel).filter(models.FixtureModel.id.in_(ids)).all()
