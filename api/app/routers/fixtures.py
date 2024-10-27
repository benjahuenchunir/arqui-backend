from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from db.database import get_db
from ..dependencies import verify_post_token
from ..schemas import response_schemas, request_schemas
from .. import crud
from fastapi import status
import sys

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
    return crud.get_fixtures(
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
    return crud.get_available_fixtures(db, page=page, count=count)


# GET /fixtures/{fixture_id}
@router.get(
    "/{fixture_id}",
    response_model=response_schemas.Fixture,
    status_code=status.HTTP_200_OK,
)
def get_fixture(fixture_id: int, db: Session = Depends(get_db)):
    """Get a fixture."""
    db_fixture = crud.get_fixture_by_id(db, fixture_id)
    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return db_fixture

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
    return crud.upsert_fixture(db, fixture)


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
    db_fixture = crud.update_fixture(db, fixture_id, fixture)

    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    crud.pay_bets(db, fixture_id)

    return db_fixture
