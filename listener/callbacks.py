import requests
import os
import logging
import sys

API_HOST = os.getenv("API_HOST")
API_PORT = os.getenv("API_PORT")
PATH_FIXTURES = os.getenv("PATH_FIXTURES")
POST_TOKEN = os.getenv("POST_TOKEN")

if not API_HOST:
    logging.error("API_HOST environment variable not set")
    sys.exit(1)

if API_PORT and API_PORT.isdigit():
    API_PORT = int(API_PORT)
else:
    logging.error("API_PORT environment variable not set or not an integer")
    sys.exit(1)

def on_info(payload):
    """Callback for a message on the info topic."""
    matches = payload["fixtures"]
    for i, match in enumerate(matches):
        logging.info("Processing match %s of %s", str(i + 1), str(len(matches)))
        try:
            response = requests.post(
                f"http://{API_HOST}:{API_PORT}/{PATH_FIXTURES}",
                json=match,
                headers={"Authorization": f"Bearer {POST_TOKEN}"},
                timeout=5,
            )
            if response.status_code != 201:
                logging.error("Failed to post match: %s", response.text)
        except requests.exceptions.RequestException as e:
            logging.error("Error posting match: %s", str(e))
    logging.info("All matches processed")

def on_validation(payload):
    """Callback for a message on the validation topic."""

def on_history(payload):
    """Callback for a message on the history topic."""  

