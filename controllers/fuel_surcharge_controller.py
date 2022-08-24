from http import HTTPStatus

import requests
from flask_restx import Namespace, Resource

from config import Config
from utilities import custom_response

fuel_surcharge_ns = Namespace("fuel_surcharge", description="Fuel Surcharge")


@fuel_surcharge_ns.route("/")
class FuelSurcharge(Resource):
    def get(self):
        gfsc_url = Config.GROUND_FUEL_SURCHARGE_URL
        pfsc_url = Config.PRIORITY_FUEL_SURCHARGE_URL

        gfsc_response = requests.get(gfsc_url)
        pfsc_response = requests.get(pfsc_url)

        response = {
            "ground": gfsc_response.json(),
            "priority": pfsc_response.json()
        }

        return custom_response("success", "Fuel Surcharge data", HTTPStatus.OK, data=response)
