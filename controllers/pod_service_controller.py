from http import HTTPStatus

from flask_restx import Namespace, Resource
from flask import request

from services.soap_requests.pod_service import pod_info
from utilities import strip_specials, custom_response

pod_service_ns = Namespace("pod_service", description="POD related services")


@pod_service_ns.route("/pod")
class POD(Resource):
    # @get_user_data
    # @cognito_auth_required
    def get(self):
        cust_id = strip_specials(request.args.get('cust_id', '')).strip()
        uid = strip_specials(request.args.get('uid', '')).strip()
        login_name = strip_specials(request.args.get('login_name', '')).strip()
        air_bill_number = request.args.get('air_bill_number', '')

        try:
            pod_info_response = pod_info(cust_id=cust_id, uid=uid, login_name=login_name,
                                         air_bill_number=air_bill_number)

            if pod_info_response[1] == "success":
                return custom_response("success", "POD info", HTTPStatus.OK, data=pod_info_response[0])
            elif pod_info_response[1] == "error":
                return custom_response("success", pod_info_response[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
