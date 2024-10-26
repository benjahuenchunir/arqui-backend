"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=missing-docstring

import logging

from fastapi import FastAPI
from celery.result import AsyncResult
from celery_config.tasks import get_user_purchases, get_future_matches, calculate_historical_accuracies, calculate_league_benefits, get_top_matches, process_webpay_payment, send_validation_result
from fastapi.exceptions import HTTPException
from job_models import UserInfo

from db.database import engine, get_db
from db import models

logging.basicConfig(level=logging.INFO)

models.Base.metadata.create_all(bind=engine)

def db():
    return next(get_db())

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
    deposit_token = user_info.deposit_token
    fixtures = db().query(models.FixtureModel).all()
    for fixture in fixtures:
        print(fixture)
    try:
        purchases_result = get_user_purchases.delay(user_id)
        purchases = purchases_result.get(timeout=10)

        team_ids = [purchase['team_id'] for purchase in purchases]
        future_matches_result = get_future_matches.delay(team_ids)
        future_matches = future_matches_result.get(timeout=10)

        accuracies_result = calculate_historical_accuracies.delay(user_id, team_ids)
        accuracies = accuracies_result.get(timeout=10)

        league_benefits_result = calculate_league_benefits.delay(accuracies, future_matches)
        league_benefits = league_benefits_result.get(timeout=10)

        top_matches_result = get_top_matches.delay(league_benefits)
        top_matches = top_matches_result.get(timeout=10)

        payment_result = process_webpay_payment.delay(user_id, deposit_token)
        payment_status = payment_result.get(timeout=10)

        validation_result = send_validation_result.delay(payment_status, top_matches)

        return {
            "message": "Job published successfully",
            "job_id": validation_result.id,
            "payment_status": payment_status,
            "top_matches": top_matches
        }

    except Exception as e:
        logging.error(f"Error processing job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process job")


@app.get("/heartbeat")
async def heartbeat():
    return True
