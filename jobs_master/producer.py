"""Subscribes to the MQTT broker and listens for messages."""

# pylint: disable=missing-docstring

import logging

from celery import chain, chord, group
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

logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.get("/job/{_id}")
async def get_job(_id: str):
    result = AsyncResult(_id)
    if result.state == "PENDING":
        return {"job_id": _id, "status": "Pending"}
    elif result.state == "SUCCESS":
        return {
            "job_id": _id,
            "status": "Completed",
            "result": result.result,
            "last_updated": result.date_done,
        }
    elif result.state == "FAILURE":
        return {"job_id": _id, "status": "Failed", "error": str(result.result)}
    else:
        return {"job_id": _id, "status": result.state}


@app.post("/job")
async def publish_message(user_info: UserInfo):
    user_id = user_info.user_id
    try:
        result_chain = chain(
            get_user_purchases.s(user_id),
            chord(
                group(get_future_matches.s(), calculate_historical_accuracies.s()),
                calculate_league_benefits.s(),
            ),
            get_top_matches.s(),
        )

        # Execute the chain and wait for the final result
        final_result = result_chain.apply_async()
        return {"job_id": final_result.id}  # type: ignore

    except Exception as e:
        logging.error(f"Error processing job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process job")


@app.get("/heartbeat")
async def heartbeat():
    return True
