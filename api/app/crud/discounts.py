from sqlalchemy.orm import Session

from db import models


def get_discount(db: Session):
    db_discount = db.query(models.DiscountModel).one_or_none()
    if db_discount is None:
        db_discount = models.DiscountModel(discount=False)
        db.add(db_discount)
        db.commit()
    return db_discount.discount


def set_discount(db: Session, discount: bool):
    db_discount = db.query(models.DiscountModel).one_or_none()
    if db_discount is None:
        db_discount = models.DiscountModel(discount=discount)
        db.add(db_discount)
    else:
        db_discount.discount = discount
    db.commit()
    db.refresh(db_discount)
    return db_discount
