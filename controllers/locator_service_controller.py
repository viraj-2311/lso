from http import HTTPStatus

from flask_restx import Namespace, Resource

from services.locator_service import get_drop_box_service_center
from services.soap_requests.locator_service import retrieve_drop_boxes, retrieve_service_areas
from utilities import custom_response, strip_specials

locator_service_ns = Namespace("locator_service", descripton="Locator Service related operation")


@locator_service_ns.route("/retrieve_drop_boxes")
class RetrieveDropBoxes(Resource):

    def get(self):
        try:
            drop_box_info = retrieve_drop_boxes()
            if drop_box_info[1] == "success":
                return custom_response("success", "Drop box info.", HTTPStatus.OK, data=drop_box_info[0])
            elif drop_box_info[1] == "error":
                return custom_response("error", drop_box_info[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@locator_service_ns.route("/retrieve_service_areas")
class RetrieveServicesAreas(Resource):

    def post(self):
        payload = locator_service_ns.payload or {}
        zip_code_filter = strip_specials(payload.get("zip_code_filter", "")).strip()
        origin_zip = strip_specials(payload.get("origin_zip", "")).strip()
        country_filter = strip_specials(payload.get("country_filter", "")).strip()
        account_number = strip_specials(payload.get("account_number", "0")).strip()

        if account_number == "0":
            account_number = 0

        try:
            service_area_info = retrieve_service_areas(account_number, zip_code_filter, origin_zip, country_filter)
            if service_area_info[1] == "success":
                return custom_response("success", "Service area info.", HTTPStatus.OK, data=service_area_info[0])
            elif service_area_info[1] == "error":
                return custom_response("error", service_area_info[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@locator_service_ns.route("/search_branches")
class SearchBranches(Resource):
    def post(self):
        payload = locator_service_ns.payload or {}
        lat = strip_specials(payload.get("lat", "")).strip()
        lng = strip_specials(payload.get("lng", "")).strip()
        service_areas = strip_specials(payload.get("service_areas", "false")).strip()
        drop_boxes = strip_specials(payload.get("drop_boxes", "false")).strip()
        # assumption is this distance passed will always be in miles
        miles = strip_specials(payload.get("distance", "")).strip()
        locator_type = ''

        if service_areas == "true" and drop_boxes == "true":
            locator_type = "Both"
            if not miles:
                miles = 50
        elif service_areas == "true":
            locator_type = "ServiceCenter"
            if not miles:
                miles = 50
        elif drop_boxes == "true":
            locator_type = "Dropbox"
            if not miles:
                miles = 5
        get_data = get_drop_box_service_center(l1=lat, g1=lng, locator_type=locator_type, miles=float(miles))
        if get_data:
            return custom_response("success", "Data", HTTPStatus.OK, data=get_data)
        else:
            return custom_response("success", "No data", HTTPStatus.OK)
