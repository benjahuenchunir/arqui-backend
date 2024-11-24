import os

from app import crud
from app.schemas import request_schemas
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.database import get_db

POST_TOKEN = os.getenv("POST_TOKEN")
BET_PRICE = os.getenv("BET_PRICE")


def verify_post_token(request: Request):
    """Verify the POST token."""
    token = request.headers.get("Authorization")
    if token != f"Bearer {POST_TOKEN}":
        raise HTTPException(status_code=403, detail="Invalid token")


def get_location(request: Request) -> str:
    """Get the location of the request."""
    # ip = request.client.host  # type: ignore
    # url = f"http://ip-api.com/json/{ip}"
    # response = requests.get(url, timeout=30)
    # response.raise_for_status()

    # location = "Unknown"
    # if response.status_code == 200:
    #     json = response.json()
    #     try:
    #         if json["status"] == "success":
    #             location = f"{json['city']}, {json['regionName']}, {json['country']}"
    #     except KeyError:
    #         pass
    # return location
    return "TODO"


def check_balance(request: request_schemas.RequestShort):
    """Check the balance of the user."""
    db: Session = next(get_db())
    user = crud.get_user(db, request.uid)
    if user:
        if user.wallet < request.quantity * int(BET_PRICE):  # type: ignore
            raise HTTPException(status_code=403, detail="Insufficient funds")

        crud.update_balance(
            db,
            user.id,  # type: ignore
            request.quantity * int(BET_PRICE),  # type: ignore
            add=False,
        )


def check_bets(request: request_schemas.RequestShort):
    """Check the number of bets."""
    db: Session = next(get_db())
    fixture = crud.get_fixture_by_id(db, request.fixture_id)
    if fixture:
        if fixture.remaining_bets < request.quantity:  # type: ignore
            raise HTTPException(status_code=403, detail="No more bets allowed")


def check_reserved_bets(request: request_schemas.RequestShort):
    """Check the number of reserved bets."""
    db: Session = next(get_db())
    db_fixture = crud.get_fixture_by_id(db, request.fixture_id)
    if db_fixture:
        match request.result:
            case db_fixture.home_team.team.name:
                if db_fixture.reserved_home < request.quantity:  # type: ignore
                    raise HTTPException(status_code=403, detail="No more bets allowed")
                return "Home"
            case db_fixture.away_team.team.name:
                if db_fixture.reserved_away < request.quantity:  # type: ignore
                    raise HTTPException(status_code=403, detail="No more bets allowed")
                return "Away"
            case "---":
                if db_fixture.reserved_draw < request.quantity:  # type: ignore
                    raise HTTPException(status_code=403, detail="No more bets allowed")
                return "Draw"

    raise HTTPException(status_code=404, detail="Fixture not found")


def check_backend_bets(request: request_schemas.Request):
    """Check the number of bets."""
    db: Session = next(get_db())
    fixture = crud.get_fixture_by_id(db, request.fixture_id)
    if fixture:
        if fixture.remaining_bets < request.quantity:  # type: ignore
            raise HTTPException(status_code=403, detail="No more bets allowed")


def get_deposit_token(request: Request) -> str:
    """Get the deposit token."""
    token = request.headers.get("Deposit-Token")
    if not token:
        token = ""
    return token


def verify_admin(user_id: str, db: Session = Depends(get_db)):
    user = crud.get_current_user(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.admin:
        raise HTTPException(status_code=403, detail="User is not an admin")
    return user
