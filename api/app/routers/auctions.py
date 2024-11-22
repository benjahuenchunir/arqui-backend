import datetime
import os
import sys
from typing import List, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.database import get_db

from .. import crud
from ..dependencies import verify_post_token
from ..schemas import request_schemas, response_schemas

PATH_AUCTIONS = os.getenv("PATH_AUCTIONS")

router = APIRouter(
    prefix=f"/{PATH_AUCTIONS}",
    tags=["fixtures"],
    responses={404: {"description": "Not found"}},
)

if not PATH_AUCTIONS:
    print("PATH_AUCTIONS environment variable not set")
    sys.exit(1)

#########################################################
#                       LISTENER                        #
#########################################################

# POST /fixtures
@router.post(
    '/',
    response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED
)
async def upsert_auction(
    auction: request_schemas.Auction,
    request: Request,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    if auction.type == "offer":
        crud.upsert_offer
    elif auction.type == "proposal":
        crud.upsert_proposal