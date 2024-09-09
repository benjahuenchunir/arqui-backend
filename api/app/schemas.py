"""Pydantic schema for the API."""

from datetime import datetime

from pydantic import BaseModel


class Status(BaseModel):
    """Base class for fixture status."""

    long: str
    short: str
    elapsed: int | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Fixture(BaseModel):
    """Base class for fixtures."""

    id: int
    referee: str | None
    timezone: str
    date: datetime
    timestamp: int
    status: Status

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class League(BaseModel):
    """Base class for leagues"""

    id: int
    name: str
    country: str
    logo: str
    flag: str | None
    season: int
    round: str

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Team(BaseModel):
    """Base class for a team"""

    id: int
    name: str
    logo: str
    winner: bool | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Teams(BaseModel):
    """Base class for teams participating in a fixture"""

    home: Team
    away: Team

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Goals(BaseModel):
    """Base class for goals scored by a team"""

    home: int | None
    away: int | None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Value(BaseModel):
    """Base class for a value"""

    value: str
    odd: float

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Odd(BaseModel):
    """Base class for an odd"""

    id: int
    name: str
    values: list[Value]

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FixtureDetails(BaseModel):
    """Base class for fixture details"""

    fixture: Fixture
    league: League
    teams: Teams
    goals: Goals
    odds: list[Odd]
    last_updated: datetime | None = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True
