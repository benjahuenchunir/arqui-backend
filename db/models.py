"""SQLAlchemy models for the database."""

import os
import sys
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

current_path = os.path.dirname(__file__)
parent_path = os.path.dirname(current_path)
parent2_path = os.path.dirname(parent_path)
sys.path.append(parent2_path)

BET_LIMMIT = os.getenv("BET_LIMMIT")
BET_LIMMIT = int(BET_LIMMIT) if BET_LIMMIT else 40


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

    remaining_bets = Column(Integer, default=BET_LIMMIT)
    reserved_home = Column(Integer, default=0)
    reserved_away = Column(Integer, default=0)
    reserved_draw = Column(Integer, default=0)

    league = relationship("LeagueModel", back_populates="fixtures")
    odds = relationship(
        "OddModel", back_populates="fixture", cascade="all, delete-orphan"
    )
    requests = relationship("RequestModel", back_populates="fixture")

    home_team = relationship(
        "FixtureTeamModel",
        primaryjoin="and_(FixtureModel.id == FixtureTeamModel.id_fixture, FixtureModel.id_home_team == FixtureTeamModel.id_team)",
        foreign_keys="[FixtureTeamModel.id_fixture, FixtureTeamModel.id_team]",
        uselist=False,
        back_populates="home_fixture",
        overlaps="away_fixture,away_team",
    )
    away_team = relationship(
        "FixtureTeamModel",
        primaryjoin="and_(FixtureModel.id == FixtureTeamModel.id_fixture, FixtureModel.id_away_team == FixtureTeamModel.id_team)",
        foreign_keys="[FixtureTeamModel.id_fixture, FixtureTeamModel.id_team]",
        uselist=False,
        back_populates="away_fixture",
        overlaps="home_fixture,home_team",
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
    home_fixture = relationship("FixtureModel", back_populates="home_team")
    away_fixture = relationship("FixtureModel", back_populates="away_team")


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

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_fixture = Column(Integer, ForeignKey("fixtures.id"))
    name = Column(String(255))

    fixture = relationship("FixtureModel", back_populates="odds")
    values = relationship(
        "OddValueModel", back_populates="odds", cascade="all, delete-orphan"
    )


class UserModel(Base):
    """Base class for users"""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    wallet = Column(Float, default=0)
    job_id = Column(String(255), nullable=True)
    admin = Column(Boolean, default=False)

    requests = relationship("RequestModel", back_populates="user")


class RequestStatusEnum(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequestModel(Base):
    """Base class for requests"""

    __tablename__ = "requests"

    request_id = Column(String(255), primary_key=True, index=True)
    group_id = Column(Integer)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))
    league_name = Column(String(255), nullable=True)
    round = Column(String(255), nullable=True)
    date = Column(DateTime, nullable=True)
    result = Column(String(255))
    deposit_token = Column(String(255), nullable=True)
    datetime = Column(String(255))
    quantity = Column(Integer)
    wallet = Column(Boolean, nullable=False)
    seller = Column(Integer, nullable=True)

    status = Column(SqlEnum(RequestStatusEnum), default=RequestStatusEnum.PENDING)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, default=None)
    url_boleta = Column(String(255), nullable=True)

    paid = Column(Boolean, default=False)

    correct = Column(Boolean, default=False)

    location = Column(String(255), nullable=True)

    fixture = relationship("FixtureModel", back_populates="requests")
    user = relationship("UserModel", back_populates="requests")


class TransactionModel(Base):
    """Base class for transactions"""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(String(255), nullable=True)
    request_id = Column(String(255))
    fixture_id = Column(Integer)
    user_id = Column(String)
    result = Column(String(255))
    quantity = Column(Integer)
    status = Column(String(255), default="pending")
    wallet = Column(Boolean, default=False)


class OfferModel(Base):
    """Base class for offers"""

    __tablename__ = "offers"

    id = Column(String, primary_key=True, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))
    league_name = Column(String(255))
    round = Column(String(255))
    result = Column(String(255))
    quantity = Column(Integer)
    group_id = Column(Integer)
    status = Column(String(255), default="available")


class ProposalModel(Base):
    """Base class for proposals"""

    __tablename__ = "proposals"

    id = Column(String, primary_key=True, index=True)
    auction_id = Column(String, ForeignKey("offers.id"))
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))
    league_name = Column(String(255))
    round = Column(String(255))
    result = Column(String(255))
    quantity = Column(Integer)
    group_id = Column(Integer)
    status = Column(String(255), default="pending")
