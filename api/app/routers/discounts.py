import os
import sys

from app.crud import discounts
from app.dependencies import verify_admin
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.database import get_db

PATH_DISCOUNTS = os.getenv("PATH_DISCOUNTS")

router = APIRouter(
    prefix=f"/{PATH_DISCOUNTS}",
    tags=["auctions"],
    responses={404: {"description": "Not found"}},
)

if not PATH_DISCOUNTS:
    print("PATH_DISCOUNTS environment variable not set")
    sys.exit(1)


# GET /discount
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def get_discount(
    db: Session = Depends(get_db),
):
    discount = discounts.get_discount(db)

    return {"discount": discount}


# POST /discount
@router.post(
    "/",
    status_code=status.HTTP_200_OK,
)
async def set_discount(
    user_id: str,
    db: Session = Depends(get_db),
):
    verify_admin(user_id=user_id, db=db)

    discount = discounts.get_discount(db)

    discounts.set_discount(db, not discount)

    return {"discount": not discount}
