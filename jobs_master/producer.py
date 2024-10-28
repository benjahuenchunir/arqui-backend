"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=missing-docstring

import logging

from fastapi import FastAPI
from celery.result import AsyncResult
from celery_config.tasks import get_user_purchases, get_future_matches, calculate_historical_accuracies, calculate_league_benefits, get_top_matches
from fastapi.exceptions import HTTPException
from job_models import UserInfo
from db import models
from typing import List, Dict

logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.get("/job/{id}")
async def get_job(_id: str):
    result = AsyncResult(_id)
    if result.state == 'PENDING':
        return {"job_id": _id, "status": "Pending"}
    elif result.state == 'SUCCESS':
        return {"job_id": _id, "status": "Completed", "result": result.result}
    elif result.state == 'FAILURE':
        return {"job_id": _id, "status": "Failed", "error": str(result.result)}
    else:
        return {"job_id": _id, "status": result.state}

@app.post("/job")
async def publish_message(user_info: UserInfo):
    user_id = user_info.user_id
    try:
        purchases_result = get_user_purchases.delay(user_id)
        purchases: List[models.RequestModel] = purchases_result.get(timeout=10)
        print("User purchases: ", purchases)
        
        team_ids = {purchase.fixture.id_home_team for purchase in purchases} | {purchase.fixture.id_away_team for purchase in purchases}
        print("Team ids: ", team_ids)
        future_matches_result = get_future_matches.delay(team_ids)
        future_matches: List[models.FixtureModel] = future_matches_result.get(timeout=10)
        print("Future matches: ", future_matches)
        
        accuracies_result = calculate_historical_accuracies.delay(future_matches, purchases)
        accuracies: Dict[int, int] = accuracies_result.get(timeout=10)

        league_benefits_result = calculate_league_benefits.delay(accuracies, future_matches)
        league_benefits = league_benefits_result.get(timeout=10)

        top_matches_result = get_top_matches.delay(league_benefits)
        top_matches = top_matches_result.get(timeout=10)

        return {
            "message": "Job published successfully",
            "top_matches": top_matches
        }

    except Exception as e:
        logging.error(f"Error processing job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process job")


@app.get("/heartbeat")
async def heartbeat():
    return True
