import json
import requests
from cachetools import LRUCache
from sd_core.cache import cache_user_credentials, clear_all_credentials
from sd_core.db_cache import delete
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

host = "http://localhost:7600/api"
cache = LRUCache(maxsize=100)
events_cache = LRUCache(maxsize=2000)

events_cache_key = "event_cache"
cache_key = "settings"


# Functions to interact with settings
def credentials():
    try:
        creds = cache_user_credentials("Sundial")
        return creds
    except Exception as e:
        logger.error(f"Error retrieving credentials from cache: {e}")
        return None


def add_settings(key, value):
    try:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        data = json.dumps({"code": key, "value": value})
        response = requests.post(host + "/0/settings", data=data, headers=headers)
        response.raise_for_status()  # Raise exception for non-2xx responses
        cache[cache_key] = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding settings: {e}")
    except Exception as e:
        logger.error(f"Unexpected error adding settings: {e}")


def cached_credentials():
    try:
        response = requests.get(host + "/0/userCredentials")
        response.raise_for_status()  # Raise exception for non-2xx responses
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching cached credentials: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching credentials: {e}")
        return None


def retrieve_settings():
    creds = credentials()
    if creds:
        sundail_token = creds.get("token")  # Safely access "token" with get()
    else:
        sundail_token = None

    try:
        sett = requests.get(host + "/0/getallsettings", headers={"Authorization": sundail_token})
        sett.raise_for_status()  # Raise exception for non-2xx responses
        settings = sett.json()
        return settings
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving settings: {e}")
        return {}  # Return empty settings as fallback
    except Exception as e:
        logger.error(f"Unexpected error retrieving settings: {e}")
        return {}  # Return empty settings as fallback


def user_status():
    creds = credentials()
    if creds:
        return creds.get('userId')  # Safely access "userId"
    return None


def idletime_settings():
    sundial_token = ""
    creds = credentials()
    if creds:
        sundial_token = creds.get("token")  # Safely access "token"

    try:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', "Authorization": sundial_token}
        response = requests.get(host + "/0/idletime", headers=headers)
        response.raise_for_status()  # Raise exception for non-2xx responses

        if response.status_code == 200:
            logger.info(f"Success: {response.json()['message']}")
        else:
            logger.warning(f"Error: {response.json().get('message', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving idle time settings: {e}")
    except Exception as e:
        logger.error(f"Unexpected error retrieving idle time settings: {e}")


def launchon_start(status):
    sundial_token = ""
    creds = credentials()
    if creds:
        sundial_token = creds.get("token")  # Safely access "token"

    try:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', "Authorization": sundial_token}
        data = json.dumps({"status": status})
        response = requests.post(host + "/0/launchOnStart", data=data, headers=headers)
        response.raise_for_status()  # Raise exception for non-2xx responses
    except requests.exceptions.RequestException as e:
        logger.error(f"Error setting launch on start: {e}")
    except Exception as e:
        logger.error(f"Unexpected error setting launch on start: {e}")


def signout():
    try:
        response = requests.get(host + "/0/signout")
        response.raise_for_status()  # Raise exception for non-2xx responses
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during signout: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during signout: {e}")
