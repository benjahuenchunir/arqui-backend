"""Auctions router."""

import os
import sys

from app import publish
from app.crud import auctions
from app.dependencies import verify_admin, verify_post_token
from app.schemas import request_schemas, response_schemas
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db

PATH_AUCTIONS = os.getenv("PATH_AUCTIONS")

router = APIRouter(
    prefix=f"/{PATH_AUCTIONS}",
    tags=["auctions"],
    responses={404: {"description": "Not found"}},
)

if not PATH_AUCTIONS:
    print("PATH_AUCTIONS environment variable not set")
    sys.exit(1)


#########################################################
#                       FRONTEND                        #
#########################################################


# POST /offers
@router.post(
    "/offers",
    response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED,
)
async def publish_offer(
    offer: request_schemas.OfferShort,
    db: Session = Depends(get_db),
):
    """Publish an offer."""

    verify_admin(user_id=offer.uid, db=db)

    return publish.create_offer(db, offer)


# GET /offers
@router.get(
    "/offers",
    response_model=list[response_schemas.Offer],
    status_code=status.HTTP_200_OK,
)
async def get_offers(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get all offers."""

    verify_admin(user_id=user_id, db=db)

    return auctions.get_offers(db)


# POST /proposals
@router.post(
    "/proposals",
    response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED,
)
async def publish_proposal(
    proposal: request_schemas.ProposalShort,
    db: Session = Depends(get_db),
):
    """Publish a proposal."""

    verify_admin(user_id=proposal.uid, db=db)

    return publish.create_proposal(db, proposal)


# GET /proposals
@router.get(
    "/proposals",
    response_model=list[response_schemas.Proposal],
    status_code=status.HTTP_200_OK,
)
async def get_proposals(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get all proposals."""

    verify_admin(user_id=user_id, db=db)

    return auctions.get_proposals(db)


# POST /accept
@router.post(
    "/accept",
    response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED,
)
async def accept_proposal(
    request: request_schemas.ProposalRequest,
    db: Session = Depends(get_db),
):
    """Accept a proposal."""

    verify_admin(user_id=request.user_id, db=db)

    print(request.proposal_id)

    proposal = auctions.get_proposal(db, request.proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return publish.create_acceptance(proposal)


# POST /reject
@router.post(
    "/reject",
    response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED,
)
async def reject_proposal(
    request: request_schemas.ProposalRequest,
    db: Session = Depends(get_db),
):
    """Reject a proposal."""

    verify_admin(user_id=request.user_id, db=db)

    proposal = auctions.get_proposal(db, request.proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return publish.create_rejection(proposal)


#########################################################
#                       BACKEND                         #
#########################################################


# POST /
@router.post(
    "/",
    response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_auction(
    auction: request_schemas.Auction,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Upsert an auction."""
    if auction.type == "offer":
        return auctions.upsert_offer(db, auction)
    elif auction.type == "proposal":
        return auctions.upsert_proposal(db, auction)
    else:
        raise HTTPException(status_code=400, detail="Invalid type")


# PATCH /
@router.patch(
    "/",
    # response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED,
)
async def update_auction(
    auction: request_schemas.Auction,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Update an auction."""

    if auction.type == "acceptance":
        auctions.handle_acceptance(db, auction)
    elif auction.type == "rejection":
        auctions.handle_rejection(db, auction)
    else:
        raise HTTPException(status_code=400, detail="Invalid type")
