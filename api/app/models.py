"""SQLAlchemy models for the database."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import relationship

from .database import Base


class StatusModel(Base):
    """Base class for fixture status."""

    __tablename__ = "status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    long = Column(String)
    short = Column(String)
    elapsed = Column(Integer, nullable=True)

    fixture_id = Column(Integer, ForeignKey("fixtures.id"))
    fixture = relationship(
        "FixtureModel",
        uselist=False,
        back_populates="status",
    )


class FixtureModel(Base):
    """Base class for fixtures."""

    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, index=True)
    referee = Column(String, nullable=True)
    timezone = Column(String)
    date = Column(DateTime)
    timestamp = Column(Integer)
    status = relationship(
        "StatusModel",
        uselist=False,
        back_populates="fixture",
        cascade="all, delete-orphan",
    )

    fixture_details_id = Column(Integer, ForeignKey("fixture_details.id"))
    fixture_details = relationship(
        "FixtureDetailsModel",
        uselist=False,
        back_populates="fixture",
    )


class LeagueModel(Base):
    """Base class for leagues"""

    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    country = Column(String)
    logo = Column(String)
    flag = Column(String, nullable=True)
    season = Column(Integer)
    round = Column(String)

    fixture_details = relationship(
        "FixtureDetailsModel",
        uselist=True,
        back_populates="league",
    )


class HomeTeamModel(Base):
    """Base class for a home team"""

    __tablename__ = "home_team"

    id = Column(Integer)
    name = Column(String)
    logo = Column(String)
    winner = Column(Boolean, nullable=True)

    teams_id = Column(Integer, ForeignKey("teams.id"))
    teams = relationship("TeamsModel", uselist=False, back_populates="home")

    __table_args__ = (PrimaryKeyConstraint("id", "teams_id"),)


class AwayTeamModel(Base):
    """Base class for an away team"""

    __tablename__ = "away_team"

    id = Column(Integer)
    name = Column(String)
    logo = Column(String)
    winner = Column(Boolean, nullable=True)

    teams_id = Column(Integer, ForeignKey("teams.id"))
    teams = relationship("TeamsModel", uselist=False, back_populates="away")

    __table_args__ = (PrimaryKeyConstraint("id", "teams_id"),)


class TeamsModel(Base):
    """Base class for teams participating in a fixture"""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    home = relationship(
        "HomeTeamModel",
        uselist=False,
        back_populates="teams",
        cascade="all, delete-orphan",
    )
    away = relationship(
        "AwayTeamModel",
        uselist=False,
        back_populates="teams",
        cascade="all, delete-orphan",
    )

    fixture_details_id = Column(Integer, ForeignKey("fixture_details.id"))
    fixture_details = relationship(
        "FixtureDetailsModel",
        uselist=False,
        back_populates="teams",
    )


class GoalsModel(Base):
    """Base class for goals scored by a team"""

    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    home = Column(Integer, nullable=True)
    away = Column(Integer, nullable=True)

    fixture_details_id = Column(Integer, ForeignKey("fixture_details.id"))
    fixture_details = relationship(
        "FixtureDetailsModel",
        uselist=False,
        back_populates="goals",
    )


class ValueModel(Base):
    """Base class for a value"""

    __tablename__ = "values"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    value = Column(String)
    odd = Column(Float)

    odds_id = Column(Integer)
    fixture_details_id = Column(Integer)

    __table_args__ = (
        ForeignKeyConstraint(
            ["odds_id", "fixture_details_id"], ["odds.id", "odds.fixture_details_id"]
        ),
    )

    odds = relationship(
        "OddModel",
        primaryjoin="and_(ValueModel.odds_id == OddModel.id, ValueModel.fixture_details_id == OddModel.fixture_details_id)",
        back_populates="values",
    )


class OddModel(Base):
    """Base class for an odd"""

    __tablename__ = "odds"

    id = Column(Integer)
    name = Column(String)

    fixture_details_id = Column(Integer, ForeignKey("fixture_details.id"))

    __table_args__ = (PrimaryKeyConstraint("id", "fixture_details_id"),)

    values = relationship(
        "ValueModel",
        back_populates="odds",
        cascade="all, delete-orphan",
    )

    fixture_details = relationship(
        "FixtureDetailsModel",
        uselist=False,
        back_populates="odds",
    )


class FixtureDetailsModel(Base):
    """Base class for fixture details"""

    __tablename__ = "fixture_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    fixture = relationship(
        "FixtureModel",
        uselist=False,
        back_populates="fixture_details",
        cascade="all, delete-orphan",
    )
    league_id = Column(Integer, ForeignKey("leagues.id"))
    league = relationship(
        "LeagueModel",
        uselist=False,
        back_populates="fixture_details",
        foreign_keys=[league_id],
    )
    teams = relationship(
        "TeamsModel",
        uselist=False,
        back_populates="fixture_details",
        cascade="all, delete-orphan",
    )
    goals = relationship(
        "GoalsModel",
        uselist=False,
        back_populates="fixture_details",
        cascade="all, delete-orphan",
    )
    odds = relationship(
        "OddModel",
        uselist=True,
        back_populates="fixture_details",
        cascade="all, delete-orphan",
    )
    last_updated = Column(DateTime)


if __name__ == "__main__":
    pass
