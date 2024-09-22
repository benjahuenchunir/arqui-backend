"""CRUD operations for the fixtures API."""

# pylint: disable=C0103

from datetime import datetime

from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import func

from . import models, broker_schema


def get_fixture_by_id(db: Session, fixture_id: int):
    """Get fixture details by fixture ID."""
    return db.query(models.FixtureModel).filter(models.FixtureModel.id == fixture_id).one_or_none()

def get_fixtures(
    db: Session,
    page: int = 0,
    count: int = 25,
    home: str | None = None,
    away: str | None = None,
    date: str | None = None,
):
    """Get fixtures from the database."""
    HomeTeam = aliased(models.TeamModel)
    AwayTeam = aliased(models.TeamModel)

    query = db.query(models.FixtureModel).join(
        models.FixtureTeamModel, models.FixtureModel.id == models.FixtureTeamModel.id_fixture
    ).join(
        HomeTeam, models.FixtureModel.id_home_team == HomeTeam.id
    ).join(
        AwayTeam, models.FixtureModel.id_away_team == AwayTeam.id
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


def upsert_fixture(db: Session, fixture: broker_schema.WholeFixture):
    """Upsert or update a fixture."""
    
    # Upsert FixtureModel
    db_fixture = db.merge(models.FixtureModel(
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
        id_league=fixture.league.id
    ))
    
    # Upsert LeagueModel
    db.merge(models.LeagueModel(
        id=fixture.league.id,
        name=fixture.league.name,
        country=fixture.league.country,
        logo_url=fixture.league.logo,
        flag_url=fixture.league.flag,
        season=fixture.league.season,
        round=fixture.league.round
    ))
    
    # Upsert TeamModel for home team
    db.merge(models.TeamModel(
        id=fixture.teams.home.id,
        name=fixture.teams.home.name,
        logo_url=fixture.teams.home.logo
    ))
    
    # Upsert TeamModel for away team
    db.merge(models.TeamModel(
        id=fixture.teams.away.id,
        name=fixture.teams.away.name,
        logo_url=fixture.teams.away.logo
    ))
    
    # Upsert FixtureTeamModel for home team
    db_fixture_home_team = db.query(models.FixtureTeamModel).filter_by(
        id_fixture=fixture.fixture.id,
        id_team=fixture.teams.home.id
    ).first()
    if db_fixture_home_team:
        db_fixture_home_team.goals = fixture.goals.home
    else:
        db_fixture_home_team = models.FixtureTeamModel(
            id_fixture=fixture.fixture.id,
            id_team=fixture.teams.home.id,
            goals=fixture.goals.home
        )
        db.add(db_fixture_home_team)
    
    # Upsert FixtureTeamModel for away team
    db_fixture_away_team = db.query(models.FixtureTeamModel).filter_by(
        id_fixture=fixture.fixture.id,
        id_team=fixture.teams.away.id
    ).first()
    if db_fixture_away_team:
        db_fixture_away_team.goals = fixture.goals.away
    else:
        db_fixture_away_team = models.FixtureTeamModel(
            id_fixture=fixture.fixture.id,
            id_team=fixture.teams.away.id,
            goals=fixture.goals.away
        )
        db.add(db_fixture_away_team)
    
    # TODO if names of odds could change its better to delete all odds and reinsert them
    # Upsert OddModel and OddValueModel
    for odd in fixture.odds:
        # Since odds have same ids for different fixtures, we need to check if they exist
        db_odd = db.query(models.OddModel).filter_by(
            id_fixture=fixture.fixture.id,
            name=odd.name # This assumes that the name of the odd for a fixture is unique
        ).first()
        
        if db_odd:
            pass # Update any future fields here
        else:
            db_odd = models.OddModel( # Autoincremented ID
                id_fixture=fixture.fixture.id,
                name=odd.name
            )
            db.add(db_odd)
        
        for value in odd.values: 
            # Since odd values do not have a unique ID, we need to check if they exist
            db_odd_value = db.query(models.OddValueModel).filter_by(
                id_odd=db_odd.id,
                bet=value.value
            ).first()
            if db_odd_value:
                db_odd_value.value = float(value.odd)
            else:
                db_odd_value = models.OddValueModel(
                    id_odd=db_odd.id,
                    value=float(value.odd),
                    bet=value.value
                )
                db.add(db_odd_value)
    
    db.commit()
    db.refresh(db_fixture)
    
    return db_fixture
