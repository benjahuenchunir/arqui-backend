import os
import sys

from app.crud import users
from app.schemas import request_schemas
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db

PATH_USERS = os.getenv("PATH_USERS")
if not PATH_USERS:
    print("PATH_USERS environment variable not set")
    sys.exit(1)

router = APIRouter(
    prefix=f"/{PATH_USERS}",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

################################################################
#                     USERS - FRONTEND                         #
################################################################


# POST /signup
@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: request_schemas.User, db: Session = Depends(get_db)):
    """Create a new user."""
    return users.create_user(db, user)


# GET /wallet/{uid}
@router.get(
    "/wallet/{uid}",
    status_code=status.HTTP_200_OK,
)
def get_wallet(uid: str, db: Session = Depends(get_db)):
    """Get the wallet of the user."""
    print("Uid is ", uid)
    user = users.get_user(db, uid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": user.wallet}


# PATCH /wallet
@router.patch(
    "/wallet",
    status_code=status.HTTP_200_OK,
)
def update_balance(
    wallet: request_schemas.Wallet,
    db: Session = Depends(get_db),
):
    """Update the balance of the user."""
    return users.update_balance(db, wallet.uid, wallet.amount)
