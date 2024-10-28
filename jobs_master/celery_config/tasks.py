import os

from celery import shared_task
from sqlalchemy import or_

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()

from typing import Dict, List, Set

from db import models
from db.database import engine, get_db

models.Base.metadata.create_all(bind=engine)


def db():
    return next(get_db())


GROUP_ID = os.getenv("GROUP_ID")

if not GROUP_ID:
    raise ValueError("GROUP_ID environment variable not set")


@shared_task
def get_user_purchases(user_id: str):
    """
    Return all the approved requests for a user.
    """
    db_requests = (
        db()
        .query(models.RequestModel)
        .filter(models.RequestModel.status == models.RequestStatusEnum.APPROVED)
        .filter(models.RequestModel.user_id == user_id)
        .filter(models.RequestModel.group_id == GROUP_ID)
        .all()
    )

    team_ids = {
        request.request_id: {
            "fixture": request.fixture_id,
            "home_team": request.fixture.id_home_team,
            "away_team": request.fixture.id_away_team,
        }
        for request in db_requests
    }
    return team_ids


@shared_task
def get_future_matches(purchases: Dict[str, Dict[str, int]]):
    """
    Return all fixtures that have not finished yet for a set of teams.
    """

    team_ids = {team_id["home_team"] for team_id in purchases.values()} | {
        team_id["away_team"] for team_id in purchases.values()
    }
    future_fixtures = (
        db()
        .query(models.FixtureModel)
        .filter(
            or_(
                models.FixtureModel.id_home_team.in_(team_ids),
                models.FixtureModel.id_away_team.in_(team_ids),
            )
        )
        .filter(models.FixtureModel.status_long != "Match Finished")
        .all()
    )

    return {"fixture_ids": [fixture.id for fixture in future_fixtures]}


@shared_task
def calculate_historical_accuracies(
    future_fixtures: Dict[str, List[int]], purchases: Dict[str, Dict[str, int]]
) -> Dict[int, int]:
    """
    Return a dictionary with the count of correct predictions for each fixture.
    """
    accuracies = {fixture.id: 0 for fixture in future_fixtures}
    for purchase in purchases:
        if purchase.fixture.status_long != "Match Finished":
            continue

        quantity_bought = purchase.quantity
        home_team = purchase.fixture.home_team.team
        away_team = purchase.fixture.away_team.team
        bet = purchase.result
        actual_winner = purchase.fixture

        # TODO no me acuerdo si result era "Home" / "Away o el nombre del equipo ganador
        if (bet == "Home" and home_team.name == actual_winner) or (
            bet == "Away" and away_team.name == actual_winner
        ):  # Si le achunto al ganador
            for (
                fixture
            ) in (
                future_fixtures
            ):  # Encuentra todas las fixtures donde al menos uno de los equipos es el mismo
                if (
                    fixture.id_home_team == home_team.id
                    or fixture.id_away_team == away_team.id
                ):
                    accuracies[fixture.id] += 1 * quantity_bought
    return accuracies


@shared_task
def calculate_league_benefits(fixtures, accuracies):
    beneficios = {fixture.id: 0 for fixture in fixtures}
    for fixture in fixtures:
        accuracy = accuracies[fixture.id]
        league_round = fixture.league.round
        match_winner_odd = next(
            (odd for odd in fixture.odds if odd.name == "Match Winner"), None
        )
        if not match_winner_odd:
            print(f"ERROR: Match {fixture.id} has no Match Winner odd")
            continue
        home_team_odd: float
        away_team_odd: float
        for odd in match_winner_odd.values:
            if odd.bet == "Home":
                home_team_odd = odd.value
            elif odd.bet == "Away":
                away_team_odd = odd.value
        if home_team_odd and away_team_odd:
            beneficios[fixture.id] = (
                accuracy * league_round / (home_team_odd + away_team_odd)
            )
        else:
            print(f"ERROR: Match {fixture.id} has no odds")
    return list(sorted(beneficios.items(), key=lambda x: x[1], reverse=True))


@shared_task
def get_top_matches(benefits):
    return benefits[:3]
