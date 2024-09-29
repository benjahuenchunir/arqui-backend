"""Pydantic schema for the API."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
    date: datetime
    timestamp: int
    status_long: str
    status_short: str
    status_elapsed: Optional[int] = None
    home_team: FixtureTeam
    away_team: FixtureTeam
    league: League
    odds: List[Odd] = []

    class Config:
        from_attributes = True

class User(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class Request(BaseModel):
    id: str
    group_id: str
    fixture_id: int
    league_name: str
    round: str
    date: str
    result: str
    deposit_token: str
    datetime: datetime
    quantity: int
    seller: int

    class Config:
        from_attributes = True

class OwnRequest(BaseModel):
    request: Request
    user: User

    class Config:
        from_attributes = True