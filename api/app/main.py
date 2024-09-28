"""Main module for the CoolGoat Async API."""

# pylint: disable=W0613

import os
if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from . import crud, models, schemas, broker_schema
from .database import engine, session_local
from typing import Optional, List

POST_TOKEN = os.getenv("POST_TOKEN")

INFO_PATH=os.getenv("INFO_PATH")
REQUESTS_PATH=os.getenv("REQUESTS_PATH")
VALIDATION_PATH=os.getenv("VALIDATION_PATH")
HISTORY_PATH=os.getenv("HISTORY_PATH")

REQUESTS_API_HOST=os.getenv("REQUESTS_API_HOST")
REQUESTS_API_PORT=os.getenv("REQUESTS_API_PORT")
PUBLISH_REQUESTS_PATH = os.getenv("PUBLISH_REQUESTS_PATH")

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

def get_db():
    """Get a database session."""
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def verify_post_token(request: Request):
    """Verify the POST token."""
    token = request.headers.get("Authorization")
    if token != f"Bearer {POST_TOKEN}":
        raise HTTPException(status_code=403, detail="Forbidden")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Favicon."""
    return FileResponse("app/favicon.ico")


@app.get("/")
def root():
    """Root path."""
    return RedirectResponse(url="/fixtures")


@app.get(
    "/fixtures",
    response_model=List[schemas.Fixture],
    status_code=status.HTTP_200_OK,
)
def get_fixtures(
    db: Session = Depends(get_db),
    page: int = 0,
    count: int = 25,
    home: Optional[str] = None,
    away: Optional[str] = None,
    date: Optional[str] = None,
):
    """Get fixtures."""
    return crud.get_fixtures(
        db, page=page, count=count, home=home, away=away, date=date
    )


@app.get(
    "/fixtures/{fixture_id}",
    response_model=schemas.Fixture,
    status_code=status.HTTP_200_OK,
)
def get_fixture(fixture_id: int, db: Session = Depends(get_db)):
    """Get a fixture."""
    db_fixture = crud.get_fixture_by_id(db, fixture_id)
    if db_fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return db_fixture


@app.post(
    f"/{INFO_PATH}",
    response_model=schemas.Fixture,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_fixture(
    fixture: broker_schema.WholeFixture,
    request: Request,
    db: Session = Depends(get_db),
    token: None = Depends(verify_post_token),
):
    """Upsert a new fixture."""
    db_fixture = crud.upsert_fixture(db, fixture)
    return db_fixture
