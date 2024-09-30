"""Pydantic schema for the API."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from datetime import datetime as dt, timezone

from uuid import UUID

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

    class Config:
        from_attributes = True

class User(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class Request(BaseModel):
    request_id: Union[UUID, str]
    group_id: Union[int, str]
    fixture_id: int
    league_name: str = Field(default="")
    round: str = Field(default="")
    date: Union[dt, str] = Field(default="")
    result: str
    deposit_token: Optional[str] = Field(default="")
    datetime: Union[dt, str] = Field(default=dt.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S UTC"))
    quantity: int
    seller: int = Field(default=0)

    @field_validator("date")
    def date_validator(cls, value):
        try:
            if isinstance(value, str):
                return dt.strptime(value, "%Y-%m-%d")
            return value
        except:
            return ""
        
    @field_validator("datetime")
    def datetime_validator(cls, value):
        try:
            if isinstance(value, dt):
                return value.strftime("%Y-%m-%dT%H:%M:%S UTC")
            return value
        except:
            return dt.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S UTC")
    
    @field_validator("request_id")
    def request_id_validator(cls, value):
        if isinstance(value, str):
            return UUID(value)
        return value
    
    @field_validator("deposit_token")
    def deposit_token_validator(cls, value):
        if type(value) != str:
            return ""
        return value

    class Config:
        from_attributes = True

class OwnRequest(BaseModel):
    request: Request
    user: User

    class Config:
        from_attributes = True