import re

import pandas as pd
import requests


def clean_phone_number(phone):
    if pd.isnull(phone):
        return None
    return re.sub(r"\D", "", phone)


def query_cnam_api(phone_number):
    api_url = f"https://cnam.bulkvs.com/?id=bfc801a9fe367fc412adafa92592cd7a&did={phone_number}&format=json"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Error querying API for {phone_number}: {e}")
        return {}
