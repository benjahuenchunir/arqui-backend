import logging
import os
import sys

import requests

API_HOST = os.getenv("API_HOST")
API_PORT = os.getenv("API_PORT")

POST_TOKEN = os.getenv("POST_TOKEN")

PATH_FIXTURES = os.getenv("PATH_FIXTURES")
PATH_REQUESTS = os.getenv("PATH_REQUESTS")

if not POST_TOKEN:
    logging.error("POST_TOKEN environment variable not set")
    sys.exit(1)

if not PATH_FIXTURES:
    print("PATH_FIXTURES environment variable not set")
    sys.exit(1)

if not PATH_REQUESTS:
    print("PATH_FIXTURES environment variable not set")
    sys.exit(1)

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


def on_history(payload):
    """Callback for a message on the history topic."""
    matches = payload["fixtures"]
    for i, match in enumerate(matches):
        logging.info("Processing match %s of %s", str(i + 1), str(len(matches)))
        try:
            response = requests.patch(
                f"http://{API_HOST}:{API_PORT}/{PATH_FIXTURES}/{int(match['fixture']['id'])}",
                json=match,
                headers={"Authorization": f"Bearer {POST_TOKEN}"},
                timeout=5,
            )
            if response.status_code != 201:
                logging.error("Failed to patch match: %s", response.text)
        except requests.exceptions.RequestException as e:
            logging.error("Error patching match: %s", str(e))
        except KeyError as e:
            logging.error("Error patching match: %s", str(e))
            logging.error("Match: %s", match)
    logging.info("All matches processed")


def on_requests(payload):
    """Callback for a message on the requests topic."""
    logging.info("Processing request")
    try:
        response = requests.post(
            f"http://{API_HOST}:{API_PORT}/{PATH_REQUESTS}",
            json=payload,
            headers={"Authorization": f"Bearer {POST_TOKEN}"},
            timeout=5,
        )
        if response.status_code != 201:
            logging.error("Failed to post request: %s", response.text)
    except requests.exceptions.RequestException as e:
        logging.error("Error processing requests: %s", str(e))


def on_validation(payload):
    """Callback for a message on the validation topic."""
    logging.info("Processing validation")
    try:
        response = requests.patch(
            f"http://{API_HOST}:{API_PORT}/{PATH_REQUESTS}/{payload['request_id']}",
            json=payload,
            headers={"Authorization": f"Bearer {POST_TOKEN}"},
            timeout=5,
        )
        if response.status_code != 200:
            logging.error("Failed to post validation: %s", response.text)
    except requests.exceptions.RequestException as e:
        logging.error("Error processing validation: %s", str(e))
