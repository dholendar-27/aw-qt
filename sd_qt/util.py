
import json
import requests
from cachetools import LRUCache
from sd_core.cache import cache_user_credentials

host = "http://localhost:7600/api"
cache = LRUCache(maxsize=100)
events_cache = LRUCache(maxsize=2000)

events_cache_key = "event_cache"
cache_key = "settings"

# Functions to interact with settings
def credentials():
    creds = cache_user_credentials("Sundial")
    return creds

def add_settings(key, value):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    data = json.dumps({"code": key, "value": value})
    settings = requests.post(host + "/0/settings", data=data, headers=headers)
    cache[cache_key] = settings.json()

def retrieve_settings():
    creds = credentials()
    if creds:
        sundail_token = creds["token"] if creds['token'] else None
    try:
        sett = requests.get(host + "/0/getallsettings", headers={"Authorization": sundail_token})
        settings = sett.json()
    except Exception as e:
        print(f"Error retrieving settings: {e}")
        settings = {}
    return settings

def user_status():
    creds = credentials()
    if creds:
        return creds['userId']

def idletime_settings(status):
    sundial_token = ""
    creds = credentials()
    print(status)
    if creds:
        sundail_token = creds["token"] if creds['token'] else None
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json',"Authorization": sundail_token}
    data = json.dumps({"status": status})
    response = requests.post(host + "/0/idletime", data=data, headers=headers)

    if response.status_code == 200:
        print(f"Success: {response.json()['message']}")
    else:
        print(f"Error: {response.json().get('message', 'Unknown error')}")



def launchon_start(status):
    sundial_token = ""
    creds = credentials()
    if creds:
        sundail_token = creds["token"] if creds['token'] else None
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json',"Authorization": sundail_token}
    data = json.dumps({"status": status})
    settings = requests.post(host + "/0/launchOnStart", data=data, headers=headers)