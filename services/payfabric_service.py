import json

import requests

from config import Config


def create_and_process_transaction(body):
    r = requests.post(url=f'{Config.PAYFABRIC_URL}/payment/api/transaction/process',
                      data=json.dumps(body),
                      headers={
                          'Content-Type': 'application/json; charset=utf-8',
                          'authorization': f"{Config.PAYFABRIC_DEVICE_ID}|{Config.PAYFABRIC_PASSWORD}"
                      })
    return r.json()


def create_credit_card(body):
    try:
        r = requests.post(url=f'{Config.PAYFABRIC_URL}/payment/api/wallet/create',
                          data=json.dumps(body),
                          headers={
                              'Content-Type': 'application/json; charset=utf-8',
                              'authorization': f"{Config.PAYFABRIC_DEVICE_ID}|{Config.PAYFABRIC_PASSWORD}"
                          })
        return r.json()
    except Exception as e:
        return e
