import requests

from config import Config


def get_featured_news():
    base_url = "https://api.webflow.com"
    request_url = f"{base_url}/collections/{Config.WEB_FLOW_COLLECTION_ID}/items"

    headers = {
        "Authorization": f"Bearer {Config.WEB_FLOW_API_TOKEN}",
        "accept-version": "1.0.0"
    }

    response = requests.get(request_url, headers=headers)

    return response.json()
