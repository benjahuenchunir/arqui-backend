"""Main module for the CoolGoat Async API."""

# pylint: disable=W0613

import os
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from . import crud, models, schemas, broker_schema
from .database import engine, session_local

POST_TOKEN = os.getenv("POST_TOKEN")

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
    response_model=list[schemas.Fixture],
    status_code=status.HTTP_200_OK,
)
def get_fixtures(
    db: Session = Depends(get_db),
    page: int = 0,
    count: int = 25,
    home: str | None = None,
    away: str | None = None,
    date: str | None = None,
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
    "/fixtures",
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
