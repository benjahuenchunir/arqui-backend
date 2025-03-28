"""Contains the response schemas for the API endpoints."""

# pylint: disable=missing-docstring

from datetime import datetime as dt
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class Team(BaseModel):

    id: int
    name: str
    logo_url: str


class FixtureTeam(BaseModel):
    goals: Optional[int] = None
    team: Optional[Team] = None


class League(BaseModel):

    id: int
    name: str
    country: str
    logo_url: str
    flag_url: Optional[str] = None
    season: int
    round: str


class OddValue(BaseModel):

    id: int
    value: float
    bet: str


class Odd(BaseModel):

    id: int
    name: str
    values: List[OddValue] = []


class Fixture(BaseModel):

    id: int
    referee: Optional[str] = None
    timezone: str
    date: dt
    timestamp: int
    status_long: str
    status_short: str
    status_elapsed: Optional[int] = None
    home_team: FixtureTeam
    away_team: FixtureTeam
    league: League
    odds: List[Odd] = []
    remaining_bets: Optional[int] = None

    class Config:
        from_attributes = True


class AvailableFixture(BaseModel):

    id: int
    referee: Optional[str] = None
    date: dt
    home_team: FixtureTeam
    away_team: FixtureTeam
    odds: List[Odd] = []
    league: League
    remaining_bets: Optional[int] = None
    reserved_home: Optional[int] = None
    reserved_away: Optional[int] = None
    reserved_draw: Optional[int] = None

    class Config:
        from_attributes = True


class RecommendedFixture(BaseModel):
    fixtures: List[AvailableFixture]
    last_updated: dt


class RequestShort(BaseModel):
    request_id: str
    status: str
    quantity: int
    result: str
    league_name: str
    url_boleta: Optional[str] = None

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
    wallet: bool
    seller: int = Field(default=0)

    class Config:
        from_attributes = True


class RequestValidation(BaseModel):
    request_id: UUID
    group_id: Union[str, int]
    seller: int = Field(default=0)
    valid: bool

    class Config:
        from_attributes = True


class Auction(BaseModel):
    auction_id: Union[str, UUID]
    proposal_id: Union[str, UUID]
    fixture_id: int
    league_name: str
    round: str
    result: str
    quantity: int
    group_id: Union[int, str]
    type: str


class Offer(BaseModel):
    auction_id: Union[str, UUID]
    fixture_id: int
    league_name: str
    round: str
    result: str
    quantity: int
    group_id: Union[int, str]
    status: str


class Proposal(BaseModel):
    auction_id: Union[str, UUID]
    proposal_id: Union[str, UUID]
    fixture_id: int
    league_name: str
    round: str
    result: str
    quantity: int
    group_id: Union[int, str]
    status: str
