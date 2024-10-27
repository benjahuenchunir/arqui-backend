from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from ..dependencies import verify_post_token, get_location, check_bets, check_balance, get_deposit_token, check_backend_bets
import os
from ..schemas import response_schemas, request_schemas
from .. import crud, publish
import asyncio
import sys

PATH_REQUESTS = os.getenv("PATH_REQUESTS")
if not PATH_REQUESTS:
    print("PATH_FIXTURES environment variable not set")
    sys.exit(1)

BET_PRICE = os.getenv("BET_PRICE")
if BET_PRICE and BET_PRICE.isdigit():
    BET_PRICE = int(BET_PRICE)
else:
    print("BET_PRICE environment variable not set or not a number")
    sys.exit(1)

router = APIRouter(
    prefix=f"/{PATH_REQUESTS}",
    tags=["requests"],
    responses={404: {"description": "Not found"}},
)


################################################################
#                   REQUESTS - FRONTEND                        #
################################################################


# GET /requests/{user_id}
@router.get(
    "/{user_id}",
    response_model=List[response_schemas.RequestShort],
    status_code=status.HTTP_200_OK,
)
def get_requests(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get requests."""
    return crud.get_requests(db, user_id)


# POST /requests/frontend
@router.post(
    "/frontend",
    response_model=response_schemas.RequestShort,
    status_code=status.HTTP_200_OK,
)
async def post_publisher_request(
    request: request_schemas.RequestShort,
    db: Session = Depends(get_db),
    location: str = Depends(get_location),
    bets: None = Depends(check_bets),
    balance: None = Depends(check_balance),
    deposit_token: str = Depends(get_deposit_token)
):
    """Post a request to the publisher."""

    if (deposit_token == "") and (balance < BET_PRICE * request.quantity):
        raise HTTPException(status_code=403, detail="Insufficient funds")

    response = publish.create_request(db, request, deposit_token)
    if response is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    uid, req = response
    asyncio.create_task(
        crud.link_request(
            db,
            request_schemas.Link(
                uid=uid,
                request_id=str(req.request_id)
            ),
        )
    )

    return req

# POST /requests/validate
@router.post(
    "/validate",
    response_model=response_schemas.RequestValidation,
    status_code=status.HTTP_200_OK,
)
async def post_publisher_validation(
    request: request_schemas.RequestValidation,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Post a validation to the publisher."""
    response = publish.create_validation(db, request)
    if response is None:
        raise HTTPException(status_code=404, detail="Request not found")

    return response

################################################################
#                   REQUESTS - BACKEND                         #
################################################################


# POST /requests
@router.post(
    "/",
    response_model=response_schemas.Request,
    status_code=status.HTTP_201_CREATED,
)
def upsert_request(
    request: request_schemas.Request,
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
@router.patch(
    "/{request_id}",
    response_model=response_schemas.Request,
    status_code=status.HTTP_200_OK,
)
def update_request(
    request_id: str,
    request: request_schemas.RequestValidation,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Update a request."""
    response = crud.update_request(db, request_id, request)
    if response is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return response

