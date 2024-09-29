"""Main module for the CoolGoat Async API."""

# pylint: disable=W0613

import os
if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from . import crud, models, schemas, broker_schema
from .database import engine, session_local
from typing import Optional, List
import sys
import requests

POST_TOKEN = os.getenv("POST_TOKEN")

REQUESTS_API_HOST=os.getenv("PUBLISHER_HOST")
REQUESTS_API_PORT=os.getenv("PUBLISHER_PORT")

PATH_FIXTURES=os.getenv("PATH_FIXTURES")

if not PATH_FIXTURES:
    print("PATH_FIXTURES environment variable not set")
    sys.exit(1)

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
    return RedirectResponse(url=PATH_FIXTURES)

@app.get(
    f"/{PATH_FIXTURES}",
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
    f"/{PATH_FIXTURES}" +"/{fixture_id}",
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
    f"/{PATH_FIXTURES}",
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

@app.get("/publisher")
def get_publisher_status():
    """Get the status of the publisher. To test API-PUBLISHER connection."""
    try:
        response = requests.get(f"http://{REQUESTS_API_HOST}:{REQUESTS_API_PORT}")
        response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_ci():
    """Just to test the CI/CD pipeline. TODO remove this endpoint."""
    return {"message": "Test CI/CD pipeline"}