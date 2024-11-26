# Import the model
from db.models import DiscountModel
from sqlalchemy.orm import Session


# Insert the initial row if it doesn't exist
def insert_initial_row(db: Session):
    try:
        # Check if the row already exists
        if not db.query(DiscountModel).filter_by(id="single_row").first():
            initial_row = DiscountModel()
            db.add(initial_row)
            db.commit()

    except Exception as e:
        db.rollback()
        raise e