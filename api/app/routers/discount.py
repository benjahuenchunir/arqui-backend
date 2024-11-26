import os
import sys

from app import crud, publish
from app.dependencies import verify_admin, verify_post_token
from app.schemas import request_schemas, response_schemas
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.database import get_db

PATH_ADMIN = os.getenv("PATH_ADMIN")

router = APIRouter(
    prefix=f"/{PATH_ADMIN}",
    tags=["auctions"],
    responses={404: {"description": "Not found"}},
)

if not PATH_ADMIN:
    print("PATH_ADMIN environment variable not set")
    sys.exit(1)

# GET /discount
@router.get(
    "/discount",
    response_model=bool,
    status_code=status.HTTP_200_OK,
)
async def discount(
    db: Session = Depends(get_db),
):
    discount = crud.get_discount(db)

    return {"discount": discount}

# POST /discount
@router.post(
    "/discount",
    response_model=bool,
    status_code=status.HTTP_200_OK,
)
async def discount(
    user_id: str,
    db: Session = Depends(get_db),
):
    verify_admin(user_id=user_id, db=db)

    discount = crud.get_discount(db)

    crud.set_discount(db, not discount)

    return {"discount": not discount}

