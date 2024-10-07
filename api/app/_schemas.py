"""Pydantic schema for the API."""

# pylint: disable=missing-docstring

from datetime import datetime as dt
from datetime import timezone
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Team(BaseModel):
    """Base class for teams."""

    id: int
    name: str
    logo_url: str

    class Config:
        from_attributes = True


class FixtureTeam(BaseModel):
    goals: Optional[int] = None
    team: Optional[Team] = None

    class Config:
        from_attributes = True


class League(BaseModel):
    """Base class for leagues"""

    id: int
    name: str
    country: str
    logo_url: str
    flag_url: Optional[str] = None
    season: int
    round: str

    class Config:
        from_attributes = True


class OddValue(BaseModel):
    """Base class for odd values"""

    id: int
    value: float
    bet: str

    class Config:
        from_attributes = True


class Odd(BaseModel):
    """Base class for odds"""

    id: int
    name: str
    values: List[OddValue] = []

    class Config:
        from_attributes = True


class Fixture(BaseModel):
    """Base class for fixtures."""

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


class Request(BaseModel):
    request_id: str
    group_id: int
    fixture_id: int
    league_name: str
    round: str
    date: dt
    result: str
    deposit_token: str
    datetime: str
    quantity: int
    seller: int

    location: str

    class Config:
        from_attributes = True


class FrontendRequest(BaseModel):
    fixture_id: int
    result: str
    quantity: int
    uid: str

    class Config:
        from_attributes = True


class Link(BaseModel):
    uid: str
    request_id: str
    location: str

    class Config:
        from_attributes = True


class FrontendUser(BaseModel):
    uid: str
    email: str

    class Config:
        from_attributes = True


class FrontendRequestResponse(BaseModel):
    request_id: str
    status: str
    quantity: int
    result: str
    league_name: str

    class Config:
        from_attributes = True


class FrontendWallet(BaseModel):
    uid: str
    amount: float

    class Config:
        from_attributes = True
