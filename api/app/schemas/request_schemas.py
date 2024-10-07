"""Contains the request schemas for the API endpoints."""

# pylint: disable=missing-docstring

from datetime import datetime as dt
from typing import List, Optional

from pydantic import BaseModel


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
