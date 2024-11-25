"""CRUD operations for auctions."""

from app.crud import fixtures
from app.schemas import request_schemas
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import models


def upsert_offer(db: Session, offer: request_schemas.Auction):
    """Upsert an offer."""

    db_fixture = fixtures.get_fixture_by_id(db, offer.fixture_id)

    if not db_fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    db_offer = models.OfferModel(
        auction_id=str(offer.auction_id),
        fixture_id=offer.fixture_id,
        league_name=offer.league_name,
        round=offer.round,
        result=offer.result,
        quantity=offer.quantity,
        group_id=offer.group_id,
    )

    match offer.result:
        case db_fixture.home_team.team.name:
            db_fixture.reserved_home -= offer.quantity  # type: ignore
        case db_fixture.away_team.team.name:
            db_fixture.reserved_away -= offer.quantity  # type: ignore
        case "---":
            db_fixture.reserved_draw -= offer.quantity  # type: ignore

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
    """Upsert a proposal."""

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
