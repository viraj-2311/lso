import json

import requests

from config import Config


def track_barcode(barcode):
    request_url = f"{Config.BARCODE_TRACK_URL}"
    request_api_key = Config.BARCODE_TRACK_LAMBDA_API_KEY
    payload = json.dumps({
        "barcode": barcode
    })

    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': request_api_key
    }

    response = requests.request("POST", request_url, headers=headers, data=payload)
    return response.json()
