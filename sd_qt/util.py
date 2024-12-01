
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
    print("############", settings.json())
    cache[cache_key] = settings.json()

def retrieve_settings():
    creds = credentials()
    sundail_token = ""
    cached_settings = cache.get(cache_key)
    if cached_settings:
        return cached_settings
    else:
        if creds:
            sundail_token = creds["token"] if creds['token'] else None
        try:
            sett = requests.get(host + "/0/getallsettings", headers={"Authorization": sundail_token})
            settings = sett.json()
            cache[cache_key] = settings  # Cache the settings
            print(settings)
        except Exception as e:
            print(f"Error retrieving settings: {e}")
            settings = {}
        return settings