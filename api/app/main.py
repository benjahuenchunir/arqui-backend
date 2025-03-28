"""Main module for the CoolGoat Async API."""

# pylint: disable=W0613

import os

from app.routers import auctions, discounts, fixtures
from app.routers import requests as requestRouter
from app.routers import tests, users
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse

from db import models
from db.database import engine

if os.getenv("ENV") != "production":
    from dotenv import load_dotenv

    load_dotenv()


PATH_FIXTURES = os.getenv("PATH_FIXTURES")


app = FastAPI(root_path="/v2")

if os.getenv("ENV") != "production":
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

models.Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(requestRouter.router)
app.include_router(fixtures.router)
app.include_router(tests.router)
app.include_router(auctions.router)
app.include_router(discounts.router)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Favicon."""
    return FileResponse("app/favicon.ico")


# /
@app.get("/")
def root():
    """Root path."""
    if PATH_FIXTURES:
        return RedirectResponse(url=PATH_FIXTURES)

    return {"error": "PATH_FIXTURES environment variable not set"}
