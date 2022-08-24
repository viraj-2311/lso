import datetime
from http import HTTPStatus

from flask_cognito import cognito_auth_required
from flask_restx import Namespace, Resource

from services.soap_requests.pricing_service import estimate_price, estimate_multiple_prices
from utilities import strip_specials, custom_response

pricing_service_ns = Namespace("pricing_service", description="Pricing service related operations")


@pricing_service_ns.route("/estimate_price")
class EstimatePrice(Resource):
    def post(self):
        payload = pricing_service_ns.payload or {}
        service_type = strip_specials(payload.get("service_type", "")).strip()
        from_zip_code = strip_specials(payload.get("from_zip_code", "")).strip()
        to_zip_code = strip_specials(payload.get("to_zip_code", "")).strip()
        to_country = strip_specials(payload.get("to_country", "")).strip()
        weight = strip_specials(payload.get("weight", "")).strip()
        declared_value = strip_specials(payload.get("declared_value", "0")).strip()
        length = strip_specials(payload.get("length", "0")).strip()
        width = strip_specials(payload.get("width", "0")).strip()
        height = strip_specials(payload.get("height", "0")).strip()
        pickup = strip_specials(payload.get("pickup", "false")).strip()
        residential_delivery = strip_specials(payload.get("residential_delivery", "false")).strip()
        lso_supplies_used = strip_specials(payload.get("lso_supplies_used", "false")).strip()
        ship_date = strip_specials(payload.get("ship_date", "")).strip()
        signature_requirement = strip_specials(payload.get("signature_requirement", "None")).strip()
        hippa = strip_specials(payload.get("hippa", "false")).strip()
        use_simple_pricing = strip_specials(payload.get("use_simple_pricing", "false")).strip()
        account_number = strip_specials(payload.get("account_number", "0")).strip()

        if account_number == "0":
            account_number = 0

        try:
            if not ship_date:
                ship_date = datetime.date.today()
            estimate_price_info = estimate_price(account_number=account_number, service_type=service_type,
                                                 from_zip_code=from_zip_code, to_zip_code=to_zip_code,
                                                 to_country=to_country, weight=weight, declared_value=declared_value,
                                                 length=length, width=width, height=height, pickup=pickup,
                                                 residential_delivery=residential_delivery,
                                                 lso_supplies_used=lso_supplies_used, ship_date=ship_date,
                                                 signature_requirement=signature_requirement, hippa=hippa,
                                                 use_simple_pricing=use_simple_pricing)
            if estimate_price_info[1] == "success":
                return custom_response("success", "Estimate price.", HTTPStatus.OK, data=estimate_price_info[0])
            elif estimate_price_info[1] == "error":
                return custom_response("error", estimate_price_info[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@pricing_service_ns.route("/estimate_multiple_prices")
class EstimateMultiplePrices(Resource):
    @cognito_auth_required
    def post(self):
        payload = pricing_service_ns.payload or {}
        request_data_list = payload.get("request_data_list", "")

        try:
            multiple_response_data = estimate_multiple_prices(request_data_list=request_data_list)

            if multiple_response_data[1] == "success":
                return custom_response("success", "Multiple Estimate Price.", HTTPStatus.OK,
                                       data=multiple_response_data[0])
            elif multiple_response_data[1] == "error":
                return custom_response("error", multiple_response_data[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@pricing_service_ns.route("/calculate_rates")
class CalculateRates(Resource):
    def post(self):
        payload = pricing_service_ns.payload or {}
        ground = strip_specials(payload.get("ground", False)).strip()
        ground = True if ground == "true" else False
        if not ground:
            service_type = ["PriorityBasic", "PriorityEarly", "GroundEarly", "PrioritySaturday", "Priority2ndDay"]
            service_type_name = ["LSO Priority Overnight", "LSO Early Overnight", "LSO Economy Next Day",
                                 "LSO Saturday", "LSO 2nd Day"]
        else:
            service_type = ["GroundBasic"]
            service_type_name = ["LSO Ground"]

        ship_date = datetime.date.today()
        ship_date += datetime.timedelta(days=1)
        while ship_date.weekday() == 5 or ship_date.weekday() == 6:
            ship_date += datetime.timedelta(days=1)

        sig_requirement = strip_specials(payload.get("sig_requirement", "None")).strip()

        if sig_requirement != "None" or sig_requirement != "General" or sig_requirement != "Adult":
            sig_requirement = "None"
        weight = strip_specials(payload.get("weight", "")).strip()
        from_zip = strip_specials(payload.get("from_zip", "")).strip()
        to_zip = strip_specials(payload.get("to_zip", "")).strip()
        pickup = strip_specials(payload.get("pickup", "false")).strip()
        use_simple = strip_specials(payload.get("use_simple", "false")).strip()
        hippa = strip_specials(payload.get("hippa", "false")).strip()
        account_number = strip_specials(payload.get("account_number", "0")).strip()

        if account_number == "0":
            account_number = 0

        request_list = []
        for types in service_type:
            request_dict = {
                "account_number": account_number,
                "service_type": types,
                "from_zip_code": from_zip,
                "to_zip_code": to_zip,
                "to_country": "UnitedStates",
                "weight": weight,
                "declared_value": "10",
                "length": "0",
                "width": "0",
                "height": "0",
                "pickup": pickup if pickup == "false" or pickup == "true" else "false",
                "residential_delivery": "false",
                "lso_supplies_used": "false",
                "ship_date": ship_date,
                "signature_requirement": sig_requirement,
                "hippa": hippa if hippa == "false" or hippa == "true" else "false",
                "use_simple_pricing": use_simple if use_simple == "false" or use_simple == "true" else "false"
            }
            request_list.append(request_dict)

        try:
            multiple_response_data = estimate_multiple_prices(request_data_list=request_list)

            if multiple_response_data[1] == "success":
                response_data_list = []
                count = 0
                for response_data in multiple_response_data[0]:
                    if response_data["priced_successfully"] == "true":
                        response_data_dict = dict()
                        response_data_dict["base_price"] = response_data["base_price"]
                        response_data_dict["fuel_surcharge"] = response_data["fuel_surcharge"]
                        response_data_dict["pickup_fee"] = response_data["pickup_fee"]
                        response_data_dict["service_charge"] = response_data["service_charge"]
                        response_data_dict["total_charge"] = response_data["total_charge"]
                        response_data_dict["zone"] = response_data["zone"]
                        response_data_dict["ShippingType"] = service_type_name[count]
                        response_data_list.append(response_data_dict)
                    count += 1

                return custom_response("success", "Multiple Estimate Price.", HTTPStatus.OK,
                                       data=response_data_list)
            elif multiple_response_data[1] == "error":
                return custom_response("error", multiple_response_data[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
