"""CRUD operations for auctions."""

from app.schemas import request_schemas
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import models


def upsert_offer(db: Session, offer: request_schemas.Auction):
    """Upsert an offer."""

    db_offer = models.OfferModel(
        id=str(offer.auction_id),
        fixture_id=offer.fixture_id,
        league_name=offer.league_name,
        round=offer.round,
        result=offer.result,
        quantity=offer.quantity,
        group_id=offer.group_id,
    )

    try:
        db.add(db_offer)
        db.commit()
    except IntegrityError as e:
        raise HTTPException(status_code=409, detail="Offer already exists") from e
    return offer


def get_offers(db: Session):
    """Get all offers."""
    return (
        db.query(models.OfferModel)
        .filter(models.OfferModel.status == "available")
        .filter(models.OfferModel.group_id != 2)
        .all()
    )


def upsert_proposal(db: Session, proposal: request_schemas.Auction):

    db_proposal = models.ProposalModel(
        auction_id=proposal.auction_id,
        fixture_id=proposal.fixture_id,
        league_name=proposal.league_name,
        round=proposal.round,
        result=proposal.result,
        quantity=proposal.quantity,
        group_id=proposal.group_id,
    )

    db.add(db_proposal)
    db.commit()
    return proposal


def update_offer(db: Session, offer_id: str, offer: request_schemas.Offer):
    db_offer = (
        db.query(models.OfferModel)
        .filter(models.OfferModel.id == offer_id)
        .one_or_none()
    )
    if db_offer is None:
        return None

    db_offer.status = offer.status

    db.commit()
    db.refresh(db_offer)
    return db_offer


def update_proposal(db: Session, proposal_id: str, proposal: request_schemas.Proposal):
    db_proposal = (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.id == proposal_id)
        .one_or_none()
    )
    if db_proposal is None:
        return None

    db_proposal.status = proposal.status

    db.commit()
    db.refresh(db_proposal)
    return db_proposal


def get_offer(db: Session, offer_id: str):
    return (
        db.query(models.OfferModel)
        .filter(models.OfferModel.id == offer_id)
        .one_or_none()
    )


def get_proposal(db: Session, proposal_id: str):
    return (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.id == proposal_id)
        .one_or_none()
    )


def get_offer_proposals(db: Session, offer_id: str):
    return (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.auction_id == offer_id)
        .all()
    )
