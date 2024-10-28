from fastapi import APIRouter, HTTPException
import requests
from fastapi.responses import JSONResponse
import os

PUBLISHER_HOST = os.getenv("PUBLISHER_HOST")
PUBLISHER_PORT = os.getenv("PUBLISHER_PORT")

JOBS_MASTER_HOST = os.getenv("JOBS_MASTER_HOST")
JOBS_MASTER_PORT = os.getenv("JOBS_MASTER_PORT")

router = APIRouter(
    tags=["requests"],
    responses={404: {"description": "Not found"}},
)

################################################################
#                           TESTS                              #
################################################################


# GET /publisher
@router.get("/publisher/heartbeat")
def get_publisher_status():
    """Get the status of the publisher. To test API-PUBLISHER connection."""
    try:
        response = requests.get(f"http://{PUBLISHER_HOST}:{PUBLISHER_PORT}", timeout=30)
        response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# GET /jobs_master
@router.get("/jobs_master/heartbeat")
def get_jobs_master_status():
    """Get the status of the jobs_master."""
    try:
        response = requests.get(f"http://{JOBS_MASTER_HOST}:{JOBS_MASTER_PORT}/heartbeat", timeout=30)
        response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# GET /jobs_master/create_job - TODO delete this endpoint
@router.get("/jobs_master/create_job/{user_id}")
def create_sample_job(user_id: str):
    try:
        payload = {
            "user_id": user_id
        }
        response = requests.post(f"http://{JOBS_MASTER_HOST}:{JOBS_MASTER_PORT}/job", json=payload, timeout=30)
        response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# GET /test
@router.get("/test")
def test_ci():
    """Just to test the CI/CD pipeline. TODO remove this endpoint."""
    return {"message": "Test CI/CD pipeline"}


# GET /health
@router.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}
