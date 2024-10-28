"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=missing-docstring

import logging
from typing import Dict, List

from celery.result import AsyncResult
from celery_config.tasks import (
    calculate_historical_accuracies,
    calculate_league_benefits,
    get_future_matches,
    get_top_matches,
    get_user_purchases,
)
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from job_models import UserInfo

from db import models

logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.get("/job/{id}")
async def get_job(_id: str):
    result = AsyncResult(_id)
    if result.state == "PENDING":
        return {"job_id": _id, "status": "Pending"}
    elif result.state == "SUCCESS":
        return {"job_id": _id, "status": "Completed", "result": result.result}
    elif result.state == "FAILURE":
        return {"job_id": _id, "status": "Failed", "error": str(result.result)}
    else:
        return {"job_id": _id, "status": result.state}


@app.post("/job")
async def publish_message(user_info: UserInfo):
    user_id = user_info.user_id
    try:
        purchases_result = get_user_purchases.delay(user_id)
        purchases: Dict[str, Dict[str, int]] = purchases_result.get(timeout=10)
        print("User purchases: ", purchases)

        future_matches_result = get_future_matches.delay(purchases)
        future_matches: List[models.FixtureModel] = future_matches_result.get(
            timeout=10
        )
        print("Future matche ids: ", future_matches)

        accuracies_result = calculate_historical_accuracies.delay(
            future_matches, purchases
        )
        accuracies: Dict[int, int] = accuracies_result.get(timeout=10)

        league_benefits_result = calculate_league_benefits.delay(
            accuracies, future_matches
        )
        league_benefits = league_benefits_result.get(timeout=10)

        top_matches_result = get_top_matches.delay(league_benefits)
        top_matches = top_matches_result.get(timeout=10)

        return {"message": "Job published successfully", "top_matches": top_matches}

    except Exception as e:
        logging.error(f"Error processing job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process job")


@app.get("/heartbeat")
async def heartbeat():
    return True
