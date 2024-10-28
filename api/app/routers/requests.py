"""Requests router."""

# pylint: disable=E0402, W0613

import asyncio
import os
import sys
from typing import List

import transbank.error.transbank_error as transbank_error
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db

from .. import crud, publish
from ..dependencies import check_backend_bets  # ? But why tho?
from ..dependencies import check_balance, check_bets, get_location, verify_post_token
from ..schemas import request_schemas, response_schemas
from ..transbank_transaction import webpay_plus_transaction
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

SESSION_ID = os.getenv("SESSION_ID")
TRANSBANK_REDIRECT_URL = os.getenv("TRANSBANK_REDIRECT_URL")

if not SESSION_ID:
    print("SESSION_ID environment variable not set")
    sys.exit(1)

if not TRANSBANK_REDIRECT_URL:
    print("TRANSBANK_REDIRECT_URL environment variable not set")
    sys.exit(1)
    
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not EMAIL:
    print("EMAIL environment variable not set")
    sys.exit(1)

if not EMAIL_PASSWORD:
    print("EMAIL_PASSWORD environment variable not set")
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


# POST /requests/webpay
@router.post(
    "/webpay",
    # response_model=response_schemas.RequestShort,
    status_code=status.HTTP_200_OK,
)
async def start_webpay_flow(
    request: request_schemas.RequestShort,
    db: Session = Depends(get_db),
    location: str = Depends(get_location),
    bets: None = Depends(check_bets),
):
    """Start the Webpay flow."""

    amount: int = request.quantity * BET_PRICE  # type: ignore
    transaction = crud.create_transaction(db, request)

    try:
        transaction_response = webpay_plus_transaction.create(
            str(transaction.id), SESSION_ID, amount, TRANSBANK_REDIRECT_URL  # type: ignore
        )
        transaction.token = transaction_response["token"]
        db.commit()

    except transbank_error.TransbankError as e:
        transaction.status = "aborted"  # type: ignore
        db.commit()
        raise HTTPException(status_code=500, detail=str(e)) from e

    publish.create_request(
        db=db,
        req=request,
        deposit_token=transaction.token,
        request_id=transaction.request_id,  # type: ignore
    )

    asyncio.create_task(
        crud.link_request(
            db,
            request_schemas.Link(
                uid=transaction.user_id,  # type: ignore
                request_id=transaction.request_id,  # type: ignore
                location=location,
            ),
        )
    )

    return {
        "url": transaction_response["url"],
        "token": transaction_response["token"],
        "amount": request.quantity,
        "price": amount,
    }


# POST /requests/commit-transaction
@router.post(
    "/commit-transaction",
    # response_model=response_schemas.TransactionResult,
    status_code=status.HTTP_200_OK,
)
async def commit_transaction(
    request: request_schemas.CommitTransaction,
    db: Session = Depends(get_db),
):
    """Commit a transaction."""

    transaction = crud.get_transaction(db, request.token)

    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    try:
        confirmed_transaction = webpay_plus_transaction.commit(request.token)
        aborted = False
    except transbank_error.TransbankError:
        transaction.status = "aborted"  # type: ignore
        db.commit()
        valid = False
        aborted = True

    if (
        confirmed_transaction["response_code"] != 0
        or confirmed_transaction["status"] != "AUTHORIZED"
    ):
        transaction.status = "rejected"  # type: ignore
        valid = False
    else:
        transaction.status = "approved"  # type: ignore
        valid = True

    publish.create_validation(
        db,
        request_schemas.RequestValidation(
            request_id=transaction.request_id,  # type: ignore
            group_id=2,
            seller=0,
            valid=valid,
        ),
    )
    
    user = crud.get_user(db, transaction.user_id) # type: ignore
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    message = MIMEMultipart()
    message["From"] = EMAIL # type: ignore
    message["To"] = user.email # type: ignore
    message["Subject"] = "Compra confirmada"
    body = f"¡Hola! Tu compra ha sido confirmada. ¡Gracias por tu apuesta! \n\n" \
              f"Fixture: {transaction.fixture_id} \n" \
                f"Cantidad: {transaction.quantity} \n" \
                f"Total: {transaction.quantity * BET_PRICE} \n\n" \
                f"¡Buena suerte!"
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, EMAIL_PASSWORD) # type: ignore
            server.send_message(message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

    db.commit()
    return {"status": "ABORTED"} if aborted else confirmed_transaction


# POST /requests/wallet
@router.post(
    "/wallet",
    status_code=status.HTTP_200_OK,
)
async def start_wallet_flow(
    request: request_schemas.RequestShort,
    db: Session = Depends(get_db),
    bets: None = Depends(check_bets),
    balance: None = Depends(check_balance),
    location: str = Depends(get_location),
):
    """Start the wallet payment method flow."""
    published_request = publish.create_request(db, request)

    asyncio.create_task(
        crud.link_request(
            db,
            request_schemas.Link(
                uid=request.uid,
                request_id=str(published_request.request_id),  # type: ignore
                location=location,
            ),
        )
    )

    return published_request


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

    db_request = crud.upsert_request(db, request, wallet=False)

    if db_request is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    return db_request


# PATCH /requests/{request_id}
@router.patch(
    "/{request_id}",
    response_model=response_schemas.Request,
    status_code=status.HTTP_200_OK,
)
async def update_request(
    request_id: str,
    request: request_schemas.RequestValidation,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Update a request."""
    response = await crud.update_request(db, request_id, request)
    if response is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return response
