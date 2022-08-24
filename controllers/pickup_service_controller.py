import datetime
from http import HTTPStatus

from flask import request
from flask_restx import Namespace, Resource
from pymssql import _mssql

from main import app_db
from services.soap_requests.pickup_service import cancel_pickup_service, schedule_pickup, get_pickup_dates
from utilities import strip_specials, custom_response

pickup_service_ns = Namespace("pickup_service", description="Pickup Service related operation")


@pickup_service_ns.route("/schedule_pickup")
class SchedulePickup(Resource):
    def post(self):
        payload = pickup_service_ns.payload or {}
        account_number = strip_specials(payload.get("account_number", "")).strip()
        phone_number = strip_specials(payload.get("phone_number", "")).strip()
        extension = strip_specials(payload.get("extension", "")).strip()
        pickup_requestor_name = strip_specials(payload.get("pickup_requestor_name", "")).strip()
        company_name = strip_specials(payload.get("company_name", "")).strip()
        line_1 = strip_specials(payload.get("line_1", "")).strip()
        line_2 = strip_specials(payload.get("line_2", "")).strip()
        line_3 = strip_specials(payload.get("line_3", "")).strip()
        city = strip_specials(payload.get("city", "")).strip()
        state = strip_specials(payload.get("state", "")).strip()
        zip_code = strip_specials(payload.get("zip_code", "")).strip()
        country = strip_specials(payload.get("country", "")).strip()
        pickup_date = strip_specials(payload.get("pickup_date", "")).strip()
        pickup_ready_time = strip_specials(payload.get("pickup_ready_time", "")).strip()
        business_close_time = strip_specials(payload.get("business_close_time", "")).strip()
        left_outside_door_after_close_time = strip_specials(
            payload.get("left_outside_door_after_close_time", "")).strip()
        dolly_required = strip_specials(payload.get("dolly_required", "")).strip()
        number_of_packages = strip_specials(payload.get("number_of_packages", "")).strip()
        total_weight = strip_specials(payload.get("total_weight", "")).strip()
        special_instructions = strip_specials(payload.get("special_instructions", "")).strip()
        hippa_pickup = strip_specials(payload.get("hippa_pickup", "")).strip()

        try:
            schedule_pickup_response = schedule_pickup(account_number=account_number, phone_number=phone_number,
                                                       extension=extension, pickup_requestor_name=pickup_requestor_name,
                                                       company_name=company_name, line_1=line_1, line_2=line_2,
                                                       line_3=line_3, city=city, state=state, zip_code=zip_code,
                                                       country=country, pickup_date=pickup_date,
                                                       pickup_ready_time=pickup_ready_time,
                                                       business_close_time=business_close_time,
                                                       left_outside_door_after_close_time=left_outside_door_after_close_time,
                                                       dolly_required=dolly_required,
                                                       number_of_packages=number_of_packages, total_weight=total_weight,
                                                       special_instructions=special_instructions,
                                                       hippa_pickup=hippa_pickup)
            if schedule_pickup_response[1] == "success":
                return custom_response("success", "Schedule pickup.", HTTPStatus.OK, data=schedule_pickup_response[0])
            elif schedule_pickup_response[1] == "error":
                return custom_response("error", schedule_pickup_response[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@pickup_service_ns.route("/cancel_pickup")
class CancelPickup(Resource):
    def post(self):
        payload = pickup_service_ns.payload or {}
        account_number = strip_specials(payload.get("account_number", "")).strip()
        confirmation_number = strip_specials(payload.get("confirmation_number", "")).strip()

        try:
            cancel_pickup = cancel_pickup_service(account_number=account_number,
                                                  confirmation_number=confirmation_number)

            if cancel_pickup == "canceled":
                return custom_response("success", "Pickup cancel.", HTTPStatus.OK)
            else:
                return custom_response("error", cancel_pickup, HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@pickup_service_ns.route("/retrieve_pickup_details")
class RetrievePickupDetails(Resource):
    def get(self):
        args = request.args
        account_number = strip_specials(args.get("account_number", "")).strip()
        confirmation_number = strip_specials(args.get("confirmation_number", "")).strip()

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            pickup_detail_query = f"SELECT * FROM webdispatch WHERE custId={account_number} AND " \
                                  f"pickupConfirmation='{confirmation_number}'"
            app_db.execute_query(cursor, pickup_detail_query)
            pickup_detail = cursor.fetchall()[0]
            if not pickup_detail:
                return custom_response("error", "No data", HTTPStatus.OK)
            else:
                response = {
                    "confirmation_number": pickup_detail.get("PickUpConfirmation", ""),
                    "contact_name": pickup_detail.get("PickupContact", ""),
                    "address_1": pickup_detail.get("Address1", ""),
                    "address_2": pickup_detail.get("Address2", ""),
                    "city": pickup_detail.get("City", ""),
                    "state": pickup_detail.get("State", ""),
                    "zip_code": pickup_detail.get("Zip", ""),
                    "phone_no": pickup_detail.get("Phone", ""),
                    "pickup_date": datetime.datetime.strftime(pickup_detail.get("PickupDate", ""), "%m/%d/%y"),
                    "number_of_packages": pickup_detail.get("PUPieces", ""),
                    "total_weight": pickup_detail.get("TotalPUWeight", ""),
                    "ready_time": pickup_detail.get("ReadyTime", ""),
                    "close_time": pickup_detail.get("CloseTime", ""),
                    "leave_outside_door": pickup_detail.get("OSD", ""),
                    "dolly_required": pickup_detail.get("Dolly", ""),
                    "special_instruction": pickup_detail.get("SpcInstructions")
                }
                return custom_response("success", "Pickup Details", HTTPStatus.OK, data=response)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)


@pickup_service_ns.route("/pickup_dates")
class PickupDates(Resource):
    def post(self):
        payload = pickup_service_ns.payload or {}
        account_number = strip_specials(payload.get("account_number", "")).strip()
        phone_number = strip_specials(payload.get("phone_number", "")).strip()
        extension = strip_specials(payload.get("extension", "")).strip()
        zip_code = strip_specials(payload.get("zip_code", "")).strip()
        time_format = "h:mm tt"

        try:
            pickup_dates = get_pickup_dates(account_number=account_number, phone_number=phone_number,
                                            extension=extension, zip_code=zip_code, time_format=time_format)

            if pickup_dates[1] == "success":
                return custom_response("success", "Pickup Dates", HTTPStatus.OK, data=pickup_dates[0])
            elif pickup_dates[1] == "error":
                return custom_response("error", pickup_dates[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@pickup_service_ns.route("/check_account_info")
class CheckAccountInfo(Resource):
    def post(self):
        payload = pickup_service_ns.payload or {}
        account_number = strip_specials(payload.get("account_number", "")).strip()
        zip_code = strip_specials(payload.get("zip_code", "")).strip()

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            check_info_query = "SELECT PhyZip FROM customerProfile WHERE "\
                               f"CustID='{account_number}' AND PhyZip='{zip_code}'"

            app_db.execute_query(cursor, check_info_query)

            check_info = cursor.fetchall()

            if not check_info:
                return custom_response("error", "Not Valid", HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("success", "Valid", HTTPStatus.OK)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
