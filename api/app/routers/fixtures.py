import datetime
import os
import sys
from typing import List, Optional

import requests
from app.crud import fixtures, users
from app.dependencies import verify_post_token
from app.schemas import request_schemas, response_schemas
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.database import get_db

PATH_FIXTURES = os.getenv("PATH_FIXTURES")

router = APIRouter(
    prefix=f"/{PATH_FIXTURES}",
    tags=["fixtures"],
    responses={404: {"description": "Not found"}},
)

if not PATH_FIXTURES:
    print("PATH_FIXTURES environment variable not set")
    sys.exit(1)


################################################################
#                   FIXTURES - FRONTEND                        #
################################################################


# GET /fixtures
@router.get(
    "/",
    response_model=List[response_schemas.Fixture],
    status_code=status.HTTP_200_OK,
)
def get_fixtures(
    db: Session = Depends(get_db),
    page: int = 0,
    count: int = 25,
    home: Optional[str] = None,
    away: Optional[str] = None,
    date: Optional[str] = None,
):
    """Get fixtures."""
    return fixtures.get_fixtures(
        db, page=page, count=count, home=home, away=away, date=date
    )


# GET /fixtures/available
@router.get(
    "/available",
    response_model=List[response_schemas.AvailableFixture],
    status_code=status.HTTP_200_OK,
)
def get_available_fixtures(
    db: Session = Depends(get_db),
    page: int = 0,
    count: int = 25,
):
    """Get available fixtures."""
    return fixtures.get_available_fixtures(db, page=page, count=count)


# GET /fixtures/{fixture_id}
@router.get(
    "/{fixture_id}",
    response_model=response_schemas.Fixture,
    status_code=status.HTTP_200_OK,
)
def get_fixture(fixture_id: int, db: Session = Depends(get_db)):
    """Get a fixture."""
    db_fixture = fixtures.get_fixture_by_id(db, fixture_id)
    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return db_fixture


# POST /fixtures/recommended
@router.post(
    "/recommended",
    status_code=status.HTTP_201_CREATED,
)
def post_recommended_fixtures(
    user_info: request_schemas.UserInfo, db: Session = Depends(get_db)
):
    """Post recommended fixtures."""
    user_id = user_info.user_id
    url = "http://arquisis-jobs-master:7998/job"
    headers = {"Content-Type": "application/json"}
    user = {"user_id": user_id}
    job_id = requests.post(url, headers=headers, json=user).json()

    db_user = users.get_user(db, user_id)
    db_user.job_id = job_id["job_id"]  # type: ignore
    db.commit()

    return job_id


# GET /fixtures/recommended/{user_id}
@router.get(
    "/recommended/{user_id}",
    response_model=response_schemas.RecommendedFixture,
    status_code=status.HTTP_200_OK,
)
def get_recommended_fixtures(user_id: str, db: Session = Depends(get_db)):
    """Get recommended fixtures."""

    db_user = users.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    job_id = db_user.job_id

    if job_id is None:
        return {"fixtures": [], "last_updated": datetime.datetime.now()}

    url = f"http://arquisis-jobs-master:7998/job/{job_id}"
    headers = {"Content-Type": "application/json"}
    user_recommendations = requests.get(url, headers=headers).json()

    if user_recommendations["status"] != "Completed":
        return {"fixtures": [], "last_updated": datetime.datetime.now()}

    recommended_fixtures = fixtures.get_recommendations(
        db, user_recommendations["result"]
    )

    return {
        "fixtures": recommended_fixtures,
        "last_updated": user_recommendations["last_updated"],
    }


################################################################
#                   FIXTURES - BACKEND                         #
################################################################


# POST /fixtures
@router.post(
    "/",
    response_model=response_schemas.Fixture,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_fixture(
    fixture: request_schemas.WholeFixture,
    request: Request,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Upsert a new fixture."""
    return fixtures.upsert_fixture(db, fixture)


# PATCH /fixtures/{fixture_id}
@router.patch(
    "/{fixture_id}",
    response_model=response_schemas.Fixture,
    status_code=status.HTTP_201_CREATED,
)
def update_fixture(
    fixture_id: int,
    fixture: request_schemas.FixtureUpdate,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Update a fixture."""
    db_fixture = fixtures.update_fixture(db, fixture_id, fixture)

    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    fixtures.pay_bets(db, fixture_id)

    return db_fixture
