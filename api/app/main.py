"""Main module for the CoolGoat Async API."""

# pylint: disable=W0613

import asyncio
import os
import sys
from typing import List, Optional

import requests
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from . import broker_schema, crud, models, publish, schemas
from .database import engine, session_local

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()

POST_TOKEN = os.getenv("POST_TOKEN")

PATH_FIXTURES = os.getenv("PATH_FIXTURES")
PATH_REQUESTS = os.getenv("PATH_REQUESTS")

PUBLISHER_HOST = os.getenv("PUBLISHER_HOST")
PUBLISHER_PORT = os.getenv("PUBLISHER_PORT")

GROUP_ID = os.getenv("GROUP_ID")

BET_PRICE = int(os.getenv("BET_PRICE"))

if not PATH_FIXTURES:
    print("PATH_FIXTURES environment variable not set")
    sys.exit(1)

if not PATH_REQUESTS:
    print("PATH_FIXTURES environment variable not set")
    sys.exit(1)

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session."""
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def verify_post_token(request: Request):
    """Verify the POST token."""
    token = request.headers.get("Authorization")
    if token != f"Bearer {POST_TOKEN}":
        raise HTTPException(status_code=403, detail="Invalid token")

        
def get_location(request: Request) -> str:
    """Get the location of the request."""
    ip = request.client.host
    url = f"http://ip-api.com/json/{ip}"
    response = requests.get(url)
    response.raise_for_status()

    location = "Unknown"
    if response.status_code == 200:
        json = response.json()
        try:
            if json["status"] == "success":
                location = f"{json['city']}, {json['regionName']}, {json['country']}"
        except KeyError:
            pass
    return location

  
def check_balance(request: schemas.FrontendRequest):
    """Check the balance of the user."""
    db: Session = next(get_db())
    user = crud.get_user(db, request.uid)
    if user:
        if user.wallet < request.quantity * BET_PRICE:  # type: ignore
            raise HTTPException(status_code=403, detail="Insufficient funds")

        crud.update_balance(
            db,
            request.uid,
            request.quantity * BET_PRICE,
            add=False,
        )


def check_bets(request: schemas.FrontendRequest):
    """Check the number of bets."""
    db: Session = next(get_db())
    fixture = crud.get_fixture_by_id(db, request.fixture_id)
    if fixture:
        if fixture.remaining_bets < request.quantity:  # type: ignore
            raise HTTPException(status_code=403, detail="No more bets allowed")


def check_backend_bets(request: broker_schema.Request):
    """Check the number of bets."""
    db: Session = next(get_db())
    fixture = crud.get_fixture_by_id(db, request.fixture_id)
    if fixture:
        if fixture.remaining_bets < request.quantity:  # type: ignore
            raise HTTPException(status_code=403, detail="No more bets allowed")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Favicon."""
    return FileResponse("app/favicon.ico")


## /
@app.get("/")
def root():
    """Root path."""
    return RedirectResponse(url=PATH_FIXTURES)


################################################################
#                   FIXTURES - FRONTEND                        #
################################################################


# GET /fixtures
@app.get(
    f"/{PATH_FIXTURES}",
    response_model=List[schemas.Fixture],
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
@app.get(
    f"/{PATH_FIXTURES}/available",
    response_model=List[schemas.Fixture],
    status_code=status.HTTP_200_OK,
)
def get_available_fixtures(db: Session = Depends(get_db)):
    """Get available fixtures."""
    return crud.get_available_fixtures(db)


# GET /fixtures/{fixture_id}
@app.get(
    f"/{PATH_FIXTURES}" + "/{fixture_id}",
    response_model=schemas.Fixture,
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
@app.post(
    f"/{PATH_FIXTURES}",
    response_model=schemas.Fixture,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_fixture(
    fixture: broker_schema.WholeFixture,
    request: Request,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Upsert a new fixture."""
    return crud.upsert_fixture(db, fixture)


# PATCH /fixtures/{fixture_id}
@app.patch(
    f"/{PATH_FIXTURES}" + "/{fixture_id}",
    response_model=schemas.Fixture,
    status_code=status.HTTP_201_CREATED,
)
async def update_fixture(
    fixture_id: int,
    fixture: broker_schema.FixtureUpdate,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Update a fixture."""
    db_fixture = crud.update_fixture(db, fixture_id, fixture)

    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    value = "Draw"
    fixture_result = "---"
    if db_fixture.home_team.goals == None or db_fixture.away_team.goals == None:
        if db_fixture.home_team.goals != None and db_fixture.away_team.goals == None:
            fixture_result = db_fixture.home_team.team.name
            value = "Home"
        elif db_fixture.home_team.goals == None and db_fixture.away_team.goals != None:
            fixture_result = db_fixture.away_team.team.name
            value = "Away"
    elif db_fixture.home_team.goals > db_fixture.away_team.goals:
        fixture_result = db_fixture.home_team.team.name
        value = "Home"
    elif db_fixture.home_team.goals < db_fixture.away_team.goals:
        fixture_result = db_fixture.away_team.team.name
        value = "Away"

    for odd in db_fixture.odds:
        if odd.name == "Match Winner":
            for v in odd.values:
                if v.bet == value:
                    odds = v.value

    # for bet in db_fixture.requests:
    #     if (
    #         bet.status == models.RequestStatusEnum.APPROVED
    #         and bet.result == fixture_result
    #     ):
    #         crud.update_balance(
    #             db, bet.user_id, bet.quantity * odds * BET_PRICE, add=True
    #         )
    return db_fixture


################################################################
#                   REQUESTS - FRONTEND                        #
################################################################


# GET /requests/{user_id}
@app.get(
    f"/{PATH_REQUESTS}" + "/{user_id}",
    response_model=List[schemas.FrontendRequestResponse],
    status_code=status.HTTP_200_OK,
)
def get_requests(user_id: str, db: Session = Depends(get_db)):
    """Get requests."""
    return crud.get_requests(db, user_id)


# POST /requests/frontend
@app.post(
    f"/{PATH_REQUESTS}/frontend",
    status_code=status.HTTP_200_OK,
)
async def post_publisher_request(
    request: schemas.FrontendRequest,
    db: Session = Depends(get_db),
    location: str = Depends(get_location),
    balance: None = Depends(check_balance),
    bets: None = Depends(check_bets),
):
    """Post a request to the publisher."""
    response = publish.create_request(db, request, location)
    if response is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    uid, req = response
    asyncio.create_task(
        crud.link_request(
            db,
            schemas.Link(
                uid=uid,
                request_id=str(req.request_id),
                location=location,
            ),
        )
    )

    return req


################################################################
#                   REQUESTS - BACKEND                         #
################################################################


# POST /requests
@app.post(
    f"/{PATH_REQUESTS}",
    status_code=status.HTTP_201_CREATED,
)
def upsert_request(
    request: broker_schema.Request,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
    bets: None = Depends(check_backend_bets),
):
    """Upsert a new request."""
    response = crud.upsert_request(db, request)

    if response is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    return response


# PATCH /requests/{request_id}
@app.patch(
    f"/{PATH_REQUESTS}" + "/{request_id}",
    status_code=status.HTTP_200_OK,
)
def update_request(
    request_id: str,
    request: broker_schema.RequestValidation,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Update a request."""
    response = crud.update_request(db, request_id, request)
    if response is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return response


################################################################
#                     USERS - FRONTEND                         #
################################################################


# POST /signup
@app.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: schemas.FrontendUser, db: Session = Depends(get_db)):
    """Create a new user."""
    return crud.create_user(db, user)


# PATCH /wallet
@app.patch(
    "/wallet",
    status_code=status.HTTP_200_OK,
)
def update_balance(
    wallet: schemas.FrontendWallet,
    db: Session = Depends(get_db),
):
    """Update the balance of the user."""
    return crud.update_balance(db, wallet.uid, wallet.amount)


################################################################
#                           TESTS                              #
################################################################


# GET /publisher
@app.get("/publisher")
def get_publisher_status():
    """Get the status of the publisher. To test API-PUBLISHER connection."""
    try:
        response = requests.get(f"http://{PUBLISHER_HOST}:{PUBLISHER_PORT}", timeout=30)
        response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# GET /test
@app.get("/test")
def test_ci():
    """Just to test the CI/CD pipeline. TODO remove this endpoint."""
    return {"message": "Test CI/CD pipeline"}


# GET /health
@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}
