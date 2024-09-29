import requests
import sys
import time

services = {
    "API": "http://localhost:8001",
    "Publisher": "http://localhost:8001/publisher",
}

def check_service(name, url):
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            print(f"{name} is running.")
        else:
            print(f"{name} is not running. Status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"{name} is not running. Error: {e}")
        return False
    return True

if __name__ == "__main__":
    all_services_running = True
    for service_name, service_url in services.items():
        time.sleep(1)
        if not check_service(service_name, service_url):
            all_services_running = False
    if not all_services_running:
        sys.exit(1)