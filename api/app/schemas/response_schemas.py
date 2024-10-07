"""Contains the response schemas for the API endpoints."""

# pylint: disable=missing-docstring

from datetime import datetime as dt
from typing import List, Optional

from pydantic import BaseModel


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

    class Config:
        from_attributes = True
