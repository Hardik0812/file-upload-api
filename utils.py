import re

import pandas as pd
import requests
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create a session for connection reuse and retry handling
session = requests.Session()

# Configure retries with backoff
retries = Retry(
    total=5,  # Number of retries
    backoff_factor=0.5,  # Wait time increases with retries (e.g., 0.5s, 1s, 2s)
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP statuses
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)


def clean_phone_number(phone):
    if pd.isnull(phone):
        return None
    # Convert to string and remove non-digit characters
    cleaned_phone = re.sub(r"\D", "", str(phone))
    # If a float exists, remove any digits after the decimal
    if "." in str(phone):
        cleaned_phone = re.sub(r"\.\d+$", "", str(phone))
    return cleaned_phone


def query_cnam_api(phone_number):
    api_url = f"https://cnam.bulkvs.com/?id=bfc801a9fe367fc412adafa92592cd7a&did={phone_number}&format=json"
    try:
        # Use the session for improved performance
        response = session.get(api_url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API returned non-200 status for {phone_number}: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Error querying API for {phone_number}: {e}")
        return {}
