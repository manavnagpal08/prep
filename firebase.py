import requests
import json
import datetime

# --- FIREBASE CONFIG --- #
FIREBASE_URL = "https://placements-3d786-default-rtdb.firebaseio.com/"  # Example: https://abc-default-rtdb.firebaseio.com

def write(path, data):
    url = f"{FIREBASE_URL}/{path}.json"
    response = requests.put(url, json=data)
    return response.json()

def push(path, data):
    url = f"{FIREBASE_URL}/{path}.json"
    response = requests.post(url, json=data)
    return response.json()

def read(path):
    url = f"{FIREBASE_URL}/{path}.json"
    response = requests.get(url)
    return response.json() if response.text else None

def update(path, data):
    url = f"{FIREBASE_URL}/{path}.json"
    response = requests.patch(url, json=data)
    return response.json()
