from fastapi import Request, HTTPException
import os
from sqlalchemy.orm import Session
from db.database import get_db
from . import crud
from .schemas import request_schemas

POST_TOKEN = os.getenv("POST_TOKEN")

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
        if user.wallet < request.quantity * BET_PRICE:  # type: ignore
            raise HTTPException(status_code=403, detail="Insufficient funds")

        crud.update_balance(
            db,
            request.uid,
            request.quantity * BET_PRICE,  # type: ignore
            add=False,
        )


def check_bets(request: request_schemas.RequestShort):
    """Check the number of bets."""
    db: Session = next(get_db())
    fixture = crud.get_fixture_by_id(db, request.fixture_id)
    if fixture:
        if fixture.remaining_bets < request.quantity:  # type: ignore
            raise HTTPException(status_code=403, detail="No more bets allowed")


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
