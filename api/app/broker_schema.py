from datetime import datetime
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

class WholeFixture(BaseModel):
    date: datetime
    id: int
    referee: Optional[str] = None
    status: Status
    timestamp: int
    timezone: str
    goals: Goals
    league: League
    odds: List[Odd]
    teams: Teams

    class Config:
        from_attributes = True