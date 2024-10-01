"""CRUD operations for the fixtures API."""

# pylint: disable=C0103

import asyncio
import os
import warnings
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import func

from . import broker_schema, models, schemas

warnings.filterwarnings("ignore", category=SAWarning)

BET_PRICE = os.getenv("BET_PRICE")


def upsert_fixture(db: Session, fixture: broker_schema.WholeFixture):
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
    fixture: broker_schema.FixtureUpdate,
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
    request: broker_schema.Request,
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
    db.refresh(db_request)
    return db_request


def update_request(
    db: Session, request_id: str, validation: broker_schema.RequestValidation
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
        db_request.status = models.RequestStatusEnum.APPROVED

    else:
        db_request.status = models.RequestStatusEnum.REJECTED
        db_fixture = (
            db.query(models.FixtureModel).filter_by(id=db_request.fixture_id).one()
        )
        db_fixture.remaining_bets += db_request.quantity

        # db_request.fixture.remaining_bets += db_request.quantity
        # if db_request.user != None:
        #     update_balance(
        #         db, db_request.user.id, db_request.quantity * BET_PRICE, add=True
        #     )

    db.commit()
    db.refresh(db_request)
    return db_request


async def link_request(db: Session, link: schemas.Link):
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
    return db_request


def create_user(db: Session, user: schemas.FrontendUser):
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
    """Get requests by user ID."""
    return db.query(models.RequestModel).filter_by(user_id=user_id).all()


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
