import requests
import sys
import time

def check_service(name, url):
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

if __name__ == "__main__":
    all_services_running = True
    time.sleep(2)
    check_service("API-PUBLISHER", "http://localhost:8001/publisher")
    if not all_services_running:
        sys.exit(1)