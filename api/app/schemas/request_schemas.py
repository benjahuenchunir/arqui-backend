"""Contains the request schemas for the API endpoints."""

# pylint: disable=missing-docstring

from datetime import datetime as dt
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class Status(BaseModel):
    elapsed: Optional[int] = None
    long: str
    short: str


class Goals(BaseModel):
    away: Optional[int] = None
    home: Optional[int] = None


class League(BaseModel):
    country: str
    flag: str
    id: int
    logo: str
    name: str
    round: str
    season: int


class OddValue(BaseModel):
    odd: str
    value: str


class Odd(BaseModel):
    id: int
    name: str
    values: List[OddValue]


class Team(BaseModel):
    id: int
    logo: str
    name: str
    winner: Optional[bool] = None


class Teams(BaseModel):
    away: Team
    home: Team


class Fixture(BaseModel):
    id: int
    referee: Optional[str] = None
    timezone: str
    date: dt
    timestamp: int
    status: Status


class WholeFixture(BaseModel):
    fixture: Fixture
    league: League
    teams: Teams
    goals: Goals
    odds: List[Odd]

    class Config:
        from_attributes = True


class FixtureUpdate(BaseModel):
    fixture: Fixture
    goals: Goals

    class Config:
        from_attributes = True


class RequestShort(BaseModel):
    fixture_id: int
    result: str
    quantity: int
    uid: str

    class Config:
        from_attributes = True


class Request(BaseModel):
    request_id: UUID
    group_id: Union[str, int]
    fixture_id: int
    league_name: str
    round: str
    date: dt
    result: str
    deposit_token: str = Field(default="")
    datetime: str
    quantity: int
    seller: int = Field(default=0)
    location: Optional[str] = None

    class Config:
        from_attributes = True


class RequestValidation(BaseModel):
    request_id: Union[str, UUID]
    group_id: Union[int, str]
    seller: int
    valid: bool

    class Config:
        from_attributes = True


class User(BaseModel):
    uid: str
    email: str
    admin: bool

    class Config:
        from_attributes = True


class Wallet(BaseModel):
    uid: str
    amount: float

    class Config:
        from_attributes = True


class Link(BaseModel):
    uid: str
    request_id: str
    location: str

    class Config:
        from_attributes = True


class CommitTransaction(BaseModel):
    token: str

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    user_id: str

class OfferShort(BaseModel):
    fixture_id: int
    result: str
    quantity: int

    class Config:
        from_atributes = True

class Offer(BaseModel):
    offer_id: UUID
    fixture_id: int
    league_name: str
    round: str
    result: str
    quantity: int
    group_id: Union[int,str]
    status: str

    class Config:
        from_attributes = True

class ProposalShort(BaseModel):
    auction_id: Union[str, UUID]
    fixture_id: int
    result: str
    quantity: int

    class Config:
        from_attributes = True

class Proposal(BaseModel):
    proposal_id: UUID
    auction_id: Union[str, UUID]
    fixture_id: int
    league_name: str
    round: str
    result: str
    quantity: int
    group_id: Union[int,str]
    status: str

    class Config:
        from_attributes = True

class Auction(BaseModel):
    auction_id: UUID
    proposal_id: Union[str, UUID]
    fixture_id: int
    league_name: str
    round: str
    result: str
    quantity: int
    group_id: Union[int,str]
    type: str

    class Config:
        from_attributes = True

# Auctions

class ProposalRequest(BaseModel):
    proposal_id: str
    user_id: str