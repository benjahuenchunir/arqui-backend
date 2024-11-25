"""CRUD operations for users."""

from app.schemas import request_schemas
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from db import models


def create_user(db: Session, user: request_schemas.User):
    """Create a new user."""
    # Check if user already exists
    db_user = db.query(models.UserModel).filter_by(id=user.uid).one_or_none()

    if db_user:
        return db_user

    db_user = models.UserModel(
        id=user.uid,
        email=user.email,
        admin=user.admin,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: str):
    """Get user details by user ID."""
    return db.query(models.UserModel).filter_by(id=user_id).one_or_none()


def update_balance(db: Session, user_id: str, amount: float, add: bool = True):
    """Update user wallet."""
    db_user = db.query(models.UserModel).filter_by(id=user_id).one_or_none()
    if db_user is None:
        return None
    if add:
        db_user.wallet += amount  # type: ignore
    else:
        db_user.wallet -= amount  # type: ignore
    db.commit()
    db.refresh(db_user)
    return db_user


def get_current_user(db: Session, user_id: str):
    return (
        db.query(models.UserModel).filter(models.UserModel.id == user_id).one_or_none()
    )
