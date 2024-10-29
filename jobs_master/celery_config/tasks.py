import os

from celery import shared_task
from sqlalchemy import or_

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()

from typing import Dict, List

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
    """Return all the approved requests for a user."""
    db_requests = (
        db()
        .query(models.RequestModel)
        .filter(models.RequestModel.status == models.RequestStatusEnum.APPROVED)
        .filter(models.RequestModel.user_id == user_id)
        .filter(models.RequestModel.group_id == GROUP_ID)
        .filter(models.RequestModel.paid == True)
        .all()
    )

    team_ids = {
        request.request_id: {
            "fixture": request.fixture_id,
            "home_team": request.fixture.id_home_team,
            "away_team": request.fixture.id_away_team,
            "correct": request.correct,
            "multiplier": request.quantity,
        }
        for request in db_requests
    }
    return team_ids


@shared_task
def get_future_matches(
    purchases: Dict[str, Dict[str, int]]
) -> Dict[str, Dict[str, int]]:
    """Return all fixtures that have not finished yet for a set of teams."""

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

    future_matches = {
        fixture.id: {
            "home_team": fixture.id_home_team,
            "away_team": fixture.id_away_team,
        }
        for fixture in future_fixtures
    }

    return future_matches  # type: ignore


@shared_task
def calculate_historical_accuracies(
    purchases: Dict[str, Dict[str, int]]
) -> Dict[str, Dict[int, int]]:
    """Return a dictionary with the count of correct predictions for each fixture."""

    accuracies = {request["home_team"]: 0 for request in purchases.values()} | {
        request["away_team"]: 0 for request in purchases.values()
    }

    for request in purchases.values():
        if request["correct"]:
            accuracies[request["home_team"]] += request["multiplier"]
            accuracies[request["away_team"]] += request["multiplier"]

    return {"accuracies": accuracies}


@shared_task
def calculate_league_benefits(results) -> Dict[str, Dict[int, float]]:
    """Return the benefits for each fixture in the league."""
    future_matches, accuracies = results
    print(future_matches)
    print(accuracies)
    db_fixtures = (
        db()
        .query(models.FixtureModel)
        .filter(models.FixtureModel.id.in_(future_matches.keys()))
        .all()
    )

    ponds = {fixture.id: 0.0 for fixture in db_fixtures}

    accuracy_values = {int(k): v for k, v in accuracies["accuracies"].items()}
    print(accuracy_values)

    for fixture in db_fixtures:
        home_team_accuracy = accuracy_values.get(fixture.id_home_team, 0)  # type: ignore
        away_team_accuracy = accuracy_values.get(fixture.id_away_team, 0)  # type: ignore
        aciertos = home_team_accuracy + away_team_accuracy
        current_round = int(fixture.league.round.split("- ")[1])
        odds = fixture.odds[0].values[0].value + fixture.odds[0].values[2].value

        ponds[fixture.id] = aciertos * current_round / odds

    return {"ponderadores": ponds}  # type: ignore


@shared_task
def get_top_matches(ponds: Dict[str, Dict[int, float]]) -> List[int]:
    """
    Return the top 3 fixtures with the highest benefits.
    """
    top_matches = ponds["ponderadores"]
    top_matches = sorted(top_matches, key=lambda x: top_matches[x], reverse=True)
    return top_matches[:3]
