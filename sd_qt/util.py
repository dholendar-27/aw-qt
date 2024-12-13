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
    try:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        data = json.dumps({"code": key, "value": value})
        settings = requests.post(host + "/0/settings", data=data, headers=headers)
        if settings.status_code == 200:
            cache[cache_key] = settings.json()
        else:
            print(f"Error adding settings: {settings.status_code} {settings.text}")
            return None
    except Exception as e:
        print(f"Error in add_settings: {e}")
        return None

def cached_credentials():
    try:
        credentials = requests.get(host + "/0/userCredentials")
        if credentials.status_code == 200:
            return credentials.json()
        else:
            print(f"Error retrieving credentials: {credentials.status_code} {credentials.text}")
            return None
    except Exception as e:
        print(f"Error in cached_credentials: {e}")
        return None

def retrieve_settings():
    creds = credentials()
    if creds:
        sundial_token = creds["token"] if creds['token'] else None
        try:
            sett = requests.get(host + "/0/getallsettings", headers={"Authorization": sundial_token})
            if sett.status_code == 200:
                settings = sett.json()
                print(settings)
                return settings
            else:
                print(f"Error retrieving settings: {sett.status_code} {sett.text}")
                return None
        except Exception as e:
            print(f"Error retrieving settings: {e}")
            return None
    return None

def user_status():
    creds = credentials()
    if creds:
        return creds['userId']
    return None

def idletime_settings():
    sundial_token = ""
    creds = credentials()
    if creds:
        sundial_token = creds["token"] if creds['token'] else None
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', "Authorization": sundial_token}
    try:
        response = requests.get(host + "/0/idletime", headers=headers)
        if response.status_code == 200:
            print(f"Success: {response.json()['message']}")
        else:
            print(f"Error: {response.json().get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error in idletime_settings: {e}")
        return None

def launchon_start(status):
    sundial_token = ""
    creds = credentials()
    if creds:
        sundial_token = creds["token"] if creds['token'] else None
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', "Authorization": sundial_token}
    data = json.dumps({"status": status})
    try:
        settings = requests.post(host + "/0/launchOnStart", data=data, headers=headers)
        if settings.status_code != 200:
            print(f"Error setting launchOnStart: {settings.status_code} {settings.text}")
            return None
    except Exception as e:
        print(f"Error in launchon_start: {e}")
        return None

def signout():
    try:
        settings = requests.get(host + "/0/signout")
        if settings.status_code != 200:
            print(f"Error signing out: {settings.status_code} {settings.text}")
            return None
    except Exception as e:
        print(f"Error in signout: {e}")
        return None
