import json

import requests

from config import Config


def generate_barcode(barcode=None):
    request_url = "https://72n8d9m8mc.execute-api.us-east-2.amazonaws.com/prd/genbarcode"
    request_api_key = Config.BARCODE_GENERATION_LAMBDA_API_KEY

    payload = json.dumps({
        "barcode": barcode
    })

    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': request_api_key
    }

    requests.post(request_url, data=payload, headers=headers)
