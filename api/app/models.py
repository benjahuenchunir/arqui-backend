"""SQLAlchemy models for the database."""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .database import Base

class FixtureModel(Base):
    """Base class for fixtures."""

    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, index=True)
    referee = Column(String(255), nullable=True)
    timezone = Column(String(255))
    date = Column(DateTime)
    timestamp = Column(Integer)
    status_long = Column(String(255))
    status_short = Column(String(255))
    status_elapsed = Column(Integer, nullable=True)
    id_league = Column(Integer, ForeignKey("leagues.id"))
    id_home_team = Column(Integer, ForeignKey("teams.id"))
    id_away_team = Column(Integer, ForeignKey("teams.id"))
    
    league = relationship("LeagueModel", back_populates="fixtures")
    odds = relationship("OddModel", back_populates="fixture", cascade="all, delete-orphan")
    home_team = relationship(
        "FixtureTeamModel",
        primaryjoin="and_(FixtureModel.id == FixtureTeamModel.id_fixture, FixtureModel.id_home_team == FixtureTeamModel.id_team)",
        foreign_keys="[FixtureTeamModel.id_fixture, FixtureTeamModel.id_team]",
        uselist=False
    )
    away_team = relationship(
        "FixtureTeamModel",
        primaryjoin="and_(FixtureModel.id == FixtureTeamModel.id_fixture, FixtureModel.id_away_team == FixtureTeamModel.id_team)",
        foreign_keys="[FixtureTeamModel.id_fixture, FixtureTeamModel.id_team]",
        uselist=False
    )

class LeagueModel(Base):
    """Base class for leagues"""

    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    country = Column(String(255))
    logo_url = Column(String(255))
    flag_url = Column(String(255), nullable=True)
    season = Column(Integer)
    round = Column(String(255))

    fixtures = relationship("FixtureModel", back_populates="league")

class TeamModel(Base):
    """Base class for teams"""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    logo_url = Column(String(255))

    fixture_teams = relationship("FixtureTeamModel", back_populates="team")

class FixtureTeamModel(Base):
    """Base class for fixture teams"""

    __tablename__ = "fixture_teams"

    id_fixture = Column(Integer, ForeignKey("fixtures.id"), primary_key=True)
    id_team = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    goals = Column(Integer, nullable=True)
    
    team = relationship("TeamModel", back_populates="fixture_teams")
    
class OddValueModel(Base):
    """Base class for odd values"""

    __tablename__ = "odd_values"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_odd = Column(Integer, ForeignKey("odds.id"))
    value = Column(Float)
    bet = Column(String(255))

    odds = relationship("OddModel", back_populates="values")

class OddModel(Base):
    """Base class for odds"""

    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, index=True)
    id_fixture = Column(Integer, ForeignKey("fixtures.id"))
    name = Column(String(255))

    fixture = relationship("FixtureModel", back_populates="odds")
    values = relationship("OddValueModel", back_populates="odds", cascade="all, delete-orphan")