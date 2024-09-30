from datetime import datetime as dt, timezone
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator

from uuid import UUID

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


class Request(BaseModel):
    request_id: Union[str, UUID]
    group_id: Union[int, str]
    fixture_id: int
    league_name: str = Field(default="")
    round: str = Field(default="")
    date: Union[dt, str] = Field(default="")
    result: str = Field(default="")
    deposit_token: Optional[str] = Field(default="")
    datetime: Union[dt, str] = Field(default=dt.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S UTC"))
    quantity: int
    seller: int = Field(default=0)

    @field_validator("result")
    def result_validator(cls, value):
        if type(value) != str:
            return ""
        return value

    @field_validator("date")
    def date_validator(cls, value):
        if isinstance(value, str):
            try:
                value = dt.strptime(value, "%Y-%m-%d")
            except ValueError:
                value=""
        elif isinstance(value, dt):
            return value
        return ""
  
    @field_validator("datetime")
    def datetime_validator(cls, value):
        try:
            if isinstance(value, dt):
                return value.strftime("%Y-%m-%dT%H:%M:%S UTC")
            elif isinstance(value, str):
                return value
        except ValueError:
            return dt.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S UTC")
    
    @field_validator("deposit_token")
    def deposit_token_validator(cls, value):
        if type(value) != str:
            return ""
        return value

    class Config:
        from_attributes = True

class RequestValidation(BaseModel):
    request_id: str
    group_id: int
    seller: int
    valid: bool

    class Config:
        from_attributes = True