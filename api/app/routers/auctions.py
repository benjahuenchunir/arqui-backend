import os
import sys

from app import publish
from app.crud import auctions
from app.dependencies import verify_admin, verify_post_token
from app.schemas import request_schemas, response_schemas
from fastapi import APIRouter, Depends, HTTPException, Request, status
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
#                       LISTENER                        #
#########################################################


# POST /
@router.post(
    "/", response_model=response_schemas.Auction, status_code=status.HTTP_201_CREATED
)
async def upsert_auction(
    auction: request_schemas.Auction,
    request: Request,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    if auction.type == "offer":
        return auctions.upsert_offer(db, auction)
    elif auction.type == "proposal":
        return auctions.upsert_proposal(db, auction)


# PATCH /
@router.patch(
    "/", response_model=response_schemas.Auction, status_code=status.HTTP_200_OK
)
async def update_auction(
    auction_id: int,
    auction: request_schemas.Auction,
    request: Request,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    if auction.type == "acceptance":
        proposal = auctions.get_proposal(db, auction.proposal_id)
        offer = auctions.get_offer(db, auction.auction_id)

        proposal.status = "accepted"
        offer.status = "sold"

        auctions.update_proposal(db, auction.proposal_id, proposal)
        auctions.update_offer(db, auction_id, offer)

        for proposal in auctions.get_offer_proposals(db, auction.auction_id):
            if proposal.status == "pending":
                proposal.status = "rejected"
                auctions.update_proposal(db, proposal.id, proposal)

        return auction

    elif auction.type == "rejection":

        proposal = auctions.get_proposal(db, auction.proposal_id)

        proposal.status = "rejected"

        auctions.update_proposal(db, auction.proposal_id, auction)

        return auction


#########################################################
#                       FRONTEND                        #
#########################################################


# POST /offer
@router.post(
    "/offer",
    response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED,
)
async def publish_offer(
    fixture_id: int,
    result: str,
    quantity: int,
    user_id: str,
    db: Session = Depends(get_db),
):
    verify_admin(user_id=user_id, db=db)

    offer = request_schemas.OfferShort(
        fixture_id=fixture_id, result=result, quantity=quantity
    )
    return publish.create_offer(db, ofr=offer)


# POST /proposal
@router.post(
    "/proposal",
    response_model=response_schemas.Auction,
    status_code=status.HTTP_201_CREATED,
)
async def publish_proposal(
    auction_id: str,
    fixture_id: int,
    result: str,
    quantity: int,
    user_id: str,
    db: Session = Depends(get_db),
):
    verify_admin(user_id=user_id, db=db)

    proposal = request_schemas.ProposalShort(
        auction_id=auction_id, fixture_id=fixture_id, result=result, quantity=quantity
    )
    return publish.create_proposal(db, prp=proposal)


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
    verify_admin(user_id=request.user_id, db=db)
    proposal = auctions.get_proposal(db, request.proposal_id)

    return publish.create_acceptance(db, proposal)


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
    verify_admin(user_id=request.user_id, db=db)
    proposal = auctions.get_proposal(db, request.proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return publish.create_rejection(db, proposal)
