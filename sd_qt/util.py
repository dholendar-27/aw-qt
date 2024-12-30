
import json
import requests
from cachetools import LRUCache
from sd_core.cache import cache_user_credentials, clear_all_credentials
from sd_core.db_cache import delete

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

def cached_credentials():
    credentials = requests.get(host + "/0/userCredentials")
    print(credentials)
    return credentials

def retrieve_settings():
    creds = credentials()
    if creds:
        sundail_token = creds["token"] if creds['token'] else None
    try:
        sett = requests.get(host + "/0/getallsettings", headers={"Authorization": sundail_token})
        settings = sett.json()
        print(settings)
    except Exception as e:
        print(f"Error retrieving settings: {e}")
        settings = {}
    return settings

def user_status():
    creds = credentials()
    if creds:
        return creds['userId']

def idletime_settings():
    sundial_token = ""
    creds = credentials()
    if creds:
        sundail_token = creds["token"] if creds['token'] else None
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json',"Authorization": sundail_token}
    response = requests.get(host + "/0/idletime", headers=headers)

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

def threshold_save(data):
    print("IN UTIL")
    creds = credentials()
    if creds:
        sundail_token = creds["token"] if creds['token'] else None
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json',"Authorization": sundail_token}
    data = json.dumps({"threshold": data})
    settings = requests.post(host + "/0/threshold", data=data, headers=headers)
    # import pdb; pdb.set_trace()


def signout():
    settings = requests.get(host + "/0/signout")