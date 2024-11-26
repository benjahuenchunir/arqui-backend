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

    try:
        db.add(db_offer)

        if db_offer.group_id == 2:  # type: ignore
            match offer.result:
                case db_fixture.home_team.team.name:
                    db_fixture.reserved_home -= offer.quantity  # type: ignore
                case db_fixture.away_team.team.name:
                    db_fixture.reserved_away -= offer.quantity  # type: ignore
                case "---":
                    db_fixture.reserved_draw -= offer.quantity  # type: ignore

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

    db_fixture = fixtures.get_fixture_by_id(db, proposal.fixture_id)

    if not db_fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    db_proposal = models.ProposalModel(
        auction_id=proposal.auction_id,
        proposal_id=str(proposal.proposal_id),
        fixture_id=proposal.fixture_id,
        league_name=proposal.league_name,
        round=proposal.round,
        result=proposal.result,
        quantity=proposal.quantity,
        group_id=proposal.group_id,
    )

    try:
        db.add(db_proposal)

        if db_proposal.group_id == 2:  # type: ignore
            match db_proposal.result:
                case db_fixture.home_team.team.name:
                    db_fixture.reserved_home -= proposal.quantity  # type: ignore
                case db_fixture.away_team.team.name:
                    db_fixture.reserved_away -= proposal.quantity  # type: ignore
                case "---":
                    db_fixture.reserved_draw -= proposal.quantity  # type: ignore

        db.commit()

    except IntegrityError as e:
        raise HTTPException(status_code=409, detail="Proposal already exists") from e

    return proposal


def get_proposals(db: Session):
    """Get all proposals to group offers."""

    db_offers = (
        db.query(models.OfferModel)
        .filter(models.OfferModel.status == "available")
        .filter(models.OfferModel.group_id == 2)
        .all()
    )

    auction_ids = [offer.auction_id for offer in db_offers]

    return (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.status == "pending")
        .filter(models.ProposalModel.auction_id.in_(auction_ids))
        .all()
    )


def handle_acceptance(db: Session, auction: request_schemas.Auction):
    """Handle proposal acceptance."""

    db_offer = (
        db.query(models.OfferModel)
        .filter(models.OfferModel.auction_id == auction.auction_id)
        .one_or_none()
    )

    if db_offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    if auction.group_id == 2:  # type: ignore
        return handle_acceptance_as_proposer(db, db_offer, auction)

    if db_offer.group_id == 2:  # type: ignore
        return handle_acceptance_as_offerer(db, db_offer, auction)

    proposals = (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.auction_id == db_offer.auction_id)
        .all()
    )

    for proposal in proposals:
        proposal.status = "accepted" if proposal.proposal_id == auction.proposal_id else "rejected"  # type: ignore

        if proposal.group_id == 2:  # type: ignore
            fixture = fixtures.get_fixture_by_id(db, proposal.fixture_id)  # type: ignore

            if not fixture:
                raise HTTPException(status_code=404, detail="Fixture not found")

            match proposal.result:
                case fixture.home_team.team.name:
                    fixture.reserved_home += proposal.quantity  # type: ignore
                case fixture.away_team.team.name:
                    fixture.reserved_away += proposal.quantity  # type: ignore
                case "---":
                    fixture.reserved_draw += proposal.quantity  # type: ignore

    db_offer.status = "closed"  # type: ignore

    db.commit()

    return auction


def handle_acceptance_as_proposer(
    db: Session, db_offer: models.OfferModel, auction: request_schemas.Auction
):
    """Handle acceptance as proposer."""

    offered_fixture = fixtures.get_fixture_by_id(db, db_offer.fixture_id)  # type: ignore

    if not offered_fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    match db_offer.result:
        case offered_fixture.home_team.team.name:
            offered_fixture.reserved_home += db_offer.quantity  # type: ignore
        case offered_fixture.away_team.team.name:
            offered_fixture.reserved_away += db_offer.quantity  # type: ignore
        case "---":
            offered_fixture.reserved_draw += db_offer.quantity  # type: ignore

    db_offer.status = "closed"  # type: ignore

    proposals = (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.auction_id == db_offer.auction_id)
        .all()
    )

    for proposal in proposals:
        proposal.status = "accepted" if proposal.proposal_id == auction.proposal_id else "rejected"  # type: ignore

    db.commit()

    return auction


def handle_acceptance_as_offerer(
    db: Session, db_offer: models.OfferModel, auction: request_schemas.Auction
):
    """Handle acceptance as offerer."""

    proposed_fixture = fixtures.get_fixture_by_id(db, auction.fixture_id)  # type: ignore

    if not proposed_fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    match auction.result:
        case proposed_fixture.home_team.team.name:
            proposed_fixture.reserved_home += auction.quantity  # type: ignore
        case proposed_fixture.away_team.team.name:
            proposed_fixture.reserved_away += auction.quantity  # type: ignore
        case "---":
            proposed_fixture.reserved_draw += auction.quantity  # type: ignore

    db_offer.status = "closed"  # type: ignore

    db_proposals = (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.auction_id == db_offer.auction_id)
        .all()
    )

    for db_proposal in db_proposals:
        db_proposal.status = "accepted" if db_proposal.proposal_id == auction.proposal_id else "rejected"  # type: ignore

    db.commit()

    return auction


def handle_rejection(db: Session, auction: request_schemas.Auction):
    """Handle proposal rejection."""

    db_proposal = (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.proposal_id == auction.proposal_id)
        .one_or_none()
    )

    if db_proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if db_proposal.group_id == 2:  # type: ignore
        return handle_group_rejection(db, db_proposal)

    db_proposal.status = "rejected"  # type: ignore

    db.commit()

    return db_proposal


def handle_group_rejection(db: Session, db_proposal: models.ProposalModel):
    """Handle group proposal rejection."""

    proposed_fixture = fixtures.get_fixture_by_id(db, db_proposal.fixture_id)  # type: ignore

    if not proposed_fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    match db_proposal.result:
        case proposed_fixture.home_team.team.name:
            proposed_fixture.reserved_home += db_proposal.quantity  # type: ignore
        case proposed_fixture.away_team.team.name:
            proposed_fixture.reserved_away += db_proposal.quantity  # type: ignore
        case "---":
            proposed_fixture.reserved_draw += db_proposal.quantity  # type: ignore

    db_proposal.status = "rejected"  # type: ignore

    db.commit()

    return db_proposal


def get_proposal(db: Session, proposal_id: str):
    """Get a proposal by ID."""
    return (
        db.query(models.ProposalModel)
        .filter(models.ProposalModel.proposal_id == proposal_id)
        .one_or_none()
    )
