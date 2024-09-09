"""CRUD operations for the fixtures API."""

# pylint: disable=C0103

from datetime import datetime

from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import func

from . import models, schemas


def get_fixture_details_by_fixture_id(db: Session, fixture_id: int):
    """Get fixture details by fixture ID."""
    return (
        db.query(models.FixtureDetailsModel)
        .join(models.FixtureModel)
        .filter(models.FixtureModel.id == fixture_id)
        .first()
    )


def get_fixtures(
    db: Session,
    page: int = 0,
    count: int = 25,
    home: str | None = None,
    away: str | None = None,
    date: str | None = None,
):
    """Get fixtures from the database."""
    query = db.query(models.FixtureDetailsModel)
    date_obj = datetime.strptime(date, "%Y-%m-%d") if date else None

    HomeTeamAlias = aliased(models.TeamsModel)
    AwayTeamAlias = aliased(models.TeamsModel)

    if home:
        query = (
            query.join(HomeTeamAlias)
            .join(models.HomeTeamModel)
            .filter(models.HomeTeamModel.name == home)
        )
    if away:
        query = (
            query.join(AwayTeamAlias)
            .join(models.AwayTeamModel)
            .filter(models.AwayTeamModel.name == away)
        )
    if date:
        query = query.join(models.FixtureModel).filter(
            func.date(models.FixtureModel.date) == date_obj
        )

    return (
        query.order_by(models.FixtureDetailsModel.last_updated.desc())
        .offset(page * count)
        .limit(count)
        .all()
    )


def create_fixture(db: Session, fixture: schemas.FixtureDetails):
    """Create a new fixture."""

    # Convert nested Pydantic models to SQLAlchemy models
    # FixtureModel
    fixture_data = fixture.fixture.model_dump()

    fixture_model = models.FixtureModel(
        status=models.StatusModel(**fixture_data.pop("status")),
        **fixture_data,
    )

    # LeagueModel
    league_model = (
        db.query(models.LeagueModel)
        .filter(models.LeagueModel.id == fixture.league.id)
        .first()
    )
    if not league_model:
        league_model = models.LeagueModel(**fixture.league.model_dump())

    # TeamsModel
    teams_model = models.TeamsModel(
        home=models.HomeTeamModel(**fixture.teams.home.model_dump()),
        away=models.AwayTeamModel(**fixture.teams.away.model_dump()),
    )

    # GoalsModel
    goals_model = models.GoalsModel(**fixture.goals.model_dump())

    # OddsModel
    odds_models = [
        models.OddModel(
            id=odd.id,
            name=odd.name,
            values=[models.ValueModel(**value.model_dump()) for value in odd.values],
        )
        for odd in fixture.odds
    ]

    # Create the main FixtureDetailsModel instance
    db_fixture = models.FixtureDetailsModel(
        fixture=fixture_model,
        league_id=league_model.id,
        league=league_model,
        teams=teams_model,
        goals=goals_model,
        odds=odds_models,
        last_updated=datetime.now(),
    )

    # Add and commit the new fixture
    db.add(db_fixture)
    db.commit()
    db.refresh(db_fixture)
    return db_fixture


def delete_fixture(db: Session, fixture_id: int):
    """Delete a fixture by ID."""
    to_delete = (
        db.query(models.FixtureDetailsModel)
        .filter(models.FixtureDetailsModel.id == fixture_id)
        .first()
    )
    db.delete(to_delete)
    return {"message": "Fixture deleted"}
