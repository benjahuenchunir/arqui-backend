import requests
import sys
import time
import os

ENV = os.getenv("ENV")
if ENV != "production":
    from dotenv import load_dotenv
    load_dotenv()

PATH_FIXTURES = os.getenv("PATH_FIXTURES")
if not PATH_FIXTURES:
    print("PATH_FIXTURES environment variable not set")
    sys.exit(1)

def check_service(name, url):
    """
    Check if the service at the given URL is running.

    Args:
        name (str): The name of the service.
        url (str): The URL of the service.

    Returns:
        bool: True if the service is running, False otherwise.
    """
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"{name} are running.")
        else:
            print(f"{name} are not running. Status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"{name} are not running. Error: {e}")
        return False
    return True

def assert_redirection(url, expected_endpoint):
    """
    Assert that accessing the given URL results in a redirection to the expected endpoint.

    Args:
        url (str): The URL to check.
        expected_endpoint (str): The expected redirection endpoint.
    """
    response = requests.get(url, allow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"] == expected_endpoint

if __name__ == "__main__":
    time.sleep(2)
    if not check_service("API-PUBLISHER", "http://localhost:8001/publisher"):
        sys.exit(1)
    
    assert_redirection("http://localhost:8001/", PATH_FIXTURES)